from pyexpat import model
from agents import Agent, WebSearchTool, ModelSettings, Runner
from pydantic import BaseModel, Field
from app import create_app, db
from app.models import FixtureFree, Tip, User
from app.services.fixtures import find_current_round
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")

class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")

class TipChoice(BaseModel):
    reason: str = Field(description="")
    choice: str = Field(description="")

def _run_agent(agent, prompt):
    return Runner.run_sync(agent, prompt)

def _get_output(result):
    if hasattr(result, "output"):
        return result.output
    if hasattr(result, "final_output"):
        return result.final_output
    return result

def run_picker_agent(match_selected=None):
    app = create_app()
    with app.app_context():
        current_round = find_current_round()

        match_ids = [str(m) for m in match_selected] if match_selected else []
        if match_ids:
            fixtures = FixtureFree.query.filter(FixtureFree.match_id.in_(match_ids)).all()
        else:
            fixtures = FixtureFree.query.filter_by(round=current_round).all()

        if not fixtures:
            print("No fixtures found for current round.")
            return

        HOW_MANY_SEARCHES = 10
        fixture = fixtures

        agent_selection = []
        for fixture in fixtures:
            match_id = fixture.match_id
            home_team = fixture.home_team or "TBD"
            away_team = fixture.away_team or "TBD"
            game_date = fixture.date.isoformat() if fixture.date else "TBD"
            game_time = fixture.time.strftime("%H:%M") if fixture.time else "TBD"

            print(f"Home team: {home_team}, Away team: {away_team}, Game date: {game_date}, Game time: {game_time}")

            ## Search Term Planner Agent ##
            INSTRUCTIONS_1 = (
                "You are a helpful \"Australian NRL (National Rugby League) performance\" research assisstant who specialises in picking winning teams in the weekly NRL competition draw "
                "In order to make an accurate prediction of who will win the game in a given upcoming match, come up with a set of web searches you will need to perform "
                "so that you have the latest and relavant information about the competing teams. "
                "You will be passing these well thoughtout web search queries to your lead web search manager. "

                "IMPORTANT INFORMATION:"
                f"The upcoming match that you are predicting is: {home_team} vs {away_team}. "
                f"You are to perform {HOW_MANY_SEARCHES} for {home_team} and {HOW_MANY_SEARCHES} for {away_team}. "

                "FURTHER CONTEXT:"
                f"Home team: {home_team}. "
                f"Away team: {away_team}. "
                f"Current Date: {game_date}. "
                f"Time of the game: {game_time}."
            )

            search_plan_agent = Agent(
                name = "Search Term Planner Agent",
                instructions = INSTRUCTIONS_1,
                model = "gpt-4o-mini",
                output_type = WebSearchPlan

            )

            ## Search Agent ##
            INSTRUCTIONS_2 = (
                "You are an Australian NRL Footy Tipping research assisstant. Given a search term, you search the web for that term and "
                "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
                "words. Capture the main points. Write succintly, no need to have complete sentences or good "
                "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
                "essence and ignore any fluff. Do not include any additional commentary other than the summary itself.\n\n"

                "IMPORTANT INFORMATION:"
                f"You are performing searches based on the upcoming game between {home_team} and {away_team}. "
                "Return equal volume of research for each team. "

                "FURTHER CONTEXT:"
                f"Home team: {home_team}. "
                f"Away team: {away_team}. "
                f"Current Date: {game_date}. "
                f"Time of the game: {game_time}."
            )

            web_search_agent = Agent(
                name = "Web Search Agent",
                instructions = INSTRUCTIONS_2,
                tools = [WebSearchTool(search_context_size = "low")],
                model = "gpt-4o-mini",
                model_settings = ModelSettings(tool_choices = "required")

            )

            ## Expert NRL Analyst ##

            INSTRUCTIONS_3 = (
                "You are an expert Australian NRL analyst. Your job is to choose the most likely winner of the upcoming match "
                "using the research summaries provided by the web search agent. Weigh recent form, injuries, team news, venue "
                "factors, head-to-head trends, travel, and schedule context. If information is missing or uncertain, make a "
                "best-effort judgment without asking follow-up questions. Provide a single tip for the winner.\n\n"
                "Output strictly as a TipChoice object with:\n"
                "- choice: the team name you are tipping (must be either the home team or the away team) IMPORTANT: Do not output anything other than the name of the team you pick\n"
                "- reason: a concise 2-4 sentence justification grounded in the provided summaries\n\n"
                "MANDATORY CHOICE OUTPUT:"
                "- You must use the same team names as the ones provided in the match context."
                "- You must output the team name in the same case as the one provided in the match context."
                "Match context: "
                f"{home_team} vs {away_team}. "
                f"Date: {game_date}. "
                f"Time: {game_time}."
            )

            team_picker_analyst = Agent(
                name="Nrl Team picker analyst",
                instructions = INSTRUCTIONS_3,
                model = "gpt-4o-mini",
                output_type = TipChoice
            )

            plan_result = _get_output(_run_agent(
                search_plan_agent,
                "Create a web search plan for the upcoming match."
            ))
            if isinstance(plan_result, dict):
                plan = WebSearchPlan(**plan_result)
            elif hasattr(plan_result, "searches"):
                plan = plan_result
            else:
                raise ValueError("Search plan output is missing 'searches'.")

            research_summaries = []
            for index, item in enumerate(plan.searches, start=1):
                summary_result = _get_output(_run_agent(web_search_agent, item.query))
                summary_text = summary_result if isinstance(summary_result, str) else str(summary_result)
                research_summaries.append(
                    f"[Search {index}] {item.query}\n"
                    f"Reason: {item.reason}\n"
                    f"Summary: {summary_text}"
                )

            analyst_prompt = (
                "Use the research summaries below to pick the winner.\n\n"
                + "\n\n".join(research_summaries)
            )

            tip_result = _get_output(_run_agent(team_picker_analyst, analyst_prompt))
            if isinstance(tip_result, dict):
                tip_choice = TipChoice(**tip_result)
            elif hasattr(tip_result, "choice"):
                tip_choice = tip_result
            else:
                raise ValueError("Tip output is missing 'choice'.")

            print(f"AI Chooses: {tip_choice.choice}")
            print(f"AI Reason: {tip_choice.reason}")
            if not (tip_choice.choice or "").strip():
                print(f"Skipping DB write for match {match_id}: empty tip choice.")
                continue
            Tip.query.filter_by(
                user_id=16,
                match=match_id,
            ).delete()
            agent_tip = Tip(
                match=match_id,
                username = "tipperbot_3000",
                user_id = 16,
                selected_team = tip_choice.choice
            )
            db.session.add(agent_tip)

        db.session.commit()
        print("Tipperbot_3000 tips have been submitted")
        

if __name__ == "__main__":
    match_id_subset = [1,2]
    run_picker_agent(match_id_subset)