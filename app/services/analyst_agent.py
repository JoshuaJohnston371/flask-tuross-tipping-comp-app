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

def _run_agent(agent, prompt):
    return Runner.run_sync(agent, prompt)

def _get_output(result):
    if hasattr(result, "output"):
        return result.output
    if hasattr(result, "final_output"):
        return result.final_output
    return result

def _build_report_for_fixture(fixture, search_count=10):
    match_id = fixture.match_id
    home_team = fixture.home_team or "TBD"
    away_team = fixture.away_team or "TBD"
    game_date = fixture.date.isoformat() if fixture.date else "TBD"
    game_time = fixture.time.strftime("%H:%M") if fixture.time else "TBD"

    print(f"Home team: {home_team}, Away team: {away_team}, Game date: {game_date}, Game time: {game_time}")

    ## Search Term Planner Agent ##
    INSTRUCTIONS_1 = (
        "You are a helpful \"Australian NRL (National Rugby League) performance\" research assisstant who specialises in "
        "finding the latest relavant nrl team stats and figures"
        "In order to make a detailed team draw analysis report, come up with a set of web searches you will need to perform "
        "so that you have the latest and relavant information about the competing teams. "
        "You will be passing these well thoughtout web search queries to your lead web search manager. "

        "# IMPORTANT INFORMATION: #"
        f"The upcoming match that you are predicting is: {home_team} vs {away_team}. "
        f"You are to perform {search_count} for {home_team} and {search_count} for {away_team}. "

        "# FURTHER MATCH CONTEXT: #"
        f"Home team: {home_team}. "
        f"Away team: {away_team}. "
        f"Current Date: {game_date}. "
        f"Time of the game: {game_time}."

        "MANATORY SEARCHES TO INCLUDE (BUT NOT LIMITED TO)"
        "- TAB betting odds for both team"
        "- Key players that are NOT playing in the upcoming match (due to injuries, suspensions, ect)"
        "- Key players that are NOT playing in the upcoming match (due to injuries, suspensions, ect)"
        "- Recent performance stats between the two teams "
        "- Oppinions about match results by proffessional commentators"
        "- Predicted winning odds"
    )

    search_plan_agent = Agent(
        name="Search Term Planner Agent",
        instructions=INSTRUCTIONS_1,
        model="gpt-4o-mini",
        output_type=WebSearchPlan

    )

    ## Search Agent ##
    INSTRUCTIONS_2 = (
        "You are an Australian NRL Footy Tipping research assisstant. Given a search term, you search the web for that term and "
        "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
        "words. Capture the main points. Write succintly, no need to have complete sentences or good "
        "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
        "essence and ignore any fluff. Do not include any additional commentary other than the summary itself.\n\n"

        "# IMPORTANT INFORMATION: #"
        f"You are performing searches based on the upcoming game between {home_team} and {away_team}. "
        "Return equal volume of research for each team. "

        "# FURTHER CONTEXT: #"
        f"Home team: {home_team}. "
        f"Away team: {away_team}. "
        f"Current Date: {game_date}. "
        f"Time of the game: {game_time}."

        "# MANATORY INFORMATION TO INCLUDE (BUT NOT LIMITED TO) #"
        "- TAB betting odds for both team"
        "- Key players that are NOT playing in the upcoming match (due to injuries, suspensions, ect)"
        "- Key players that are playing in the upcoming match (due to injuries, suspensions, ect)"
        "- Recent performance stats between the two teams "
        "- Oppinions about match results by proffessional commentators"
        "- Predicted winning odds"
    )

    web_search_agent = Agent(
        name="Web Search Agent",
        instructions=INSTRUCTIONS_2,
        tools=[WebSearchTool(search_context_size="low")],
        model="gpt-4o-mini",
        model_settings=ModelSettings(tool_choices="required")

    )

    ## Expert NRL Analyst ##

    INSTRUCTIONS_3 = (
        "You are an expert Australian NRL analyst. Your job is to preduce an insightful report on the competing teams in an upcoming match "
        "using the research summaries provided by the web search agent. Weigh recent form, injuries, team news, venue "
        "factors, head-to-head trends, travel, and schedule context. If information is missing or uncertain, make a "
        "best-effort judgment without asking follow-up questions.\n\n"

        "FURTHER CONTEXT:"
        f"Home team: {home_team}. "
        f"Away team: {away_team}. "
        f"Current Date: {game_date}. "
        f"Time of the game: {game_time}."

        "# MANATORY INFORMATION TO INCLUDE (BUT NOT LIMITED TO) #"
        "- TAB betting odds for both team"
        "- Key players that are NOT playing in the upcoming match (due to injuries, suspensions, ect)"
        "- Key players that are playing in the upcoming match (due to injuries, suspensions, ect)"
        "- Recent performance stats between the two teams "
        "- Oppinions about match results by proffessional commentators"
        "- Predicted winning odds"

        "# OUTPUT FORMAT #"
        "You output succinct markdown that follows the below heading form. Dont create any unnecessary space, make it a tight nice looking report"
        "- Make sure your report is well structured and easy to read. Assume your audience is NRL punters that are doing research on who they should bet on"
        "- The audience you are presenting to ar between 50 - 60 years old so they will appriciate clarity and not word heavy paragraphs"
        "- Make statistics clear and consise, dont bury statistics in paragraphs, example: "
        "   - TAB ODDS: Dragons paying $2.40, Tigers paying $1.30"

        "# ALWAYS OUTPUT YOUR REPORT WITH THE FOLLOWING HEADING STRUCTURE IN MARKDOWN (IF DATA AVAILABLE)#"
        """
##🤖📊 Match Intelligence Report
### Match: team 1 vs. team 2
**Date:** 
**Kick-off Time:** 
**Venue:** 
---
### TAB Betting Odds
- **Head-to-Head:**
- **Line Bet:**
- **Total Points Over/Under:**
---
### Key Players Unavailable
- **team 1**
- **team 2**
---
### Key Players Available
- **team 1**
- **team 2**
---
### Recent Performance Stats
---
### Recent Form
- **team 1**
- **team 2**
---
### Commentators' Opinions
---
### Summary of Key Factors
---
### Conclusion
### Predicted Winning Odds:
Punter recommendation: 
                """
    )

    nrl_analyst = Agent(
        name="Nrl Team picker analyst",
        instructions=INSTRUCTIONS_3,
        model="gpt-4o-mini",
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
        "Use the research summaries below to write an analysis report\n\n"
        + "\n\n".join(research_summaries)
    )

    report = _get_output(_run_agent(nrl_analyst, analyst_prompt))
    return report

def generate_match_report(match_id, search_count=10):
    if not OPENAI_API_KEY:
        return None
    app = create_app()
    with app.app_context():
        fixture = FixtureFree.query.filter_by(match_id=match_id).first()
        if not fixture:
            return None
        return _build_report_for_fixture(fixture, search_count=search_count)

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

        fixture = fixtures

        agent_selection = []
        for fixture in fixtures:
            report = _build_report_for_fixture(fixture)
            print("Analyst Report:")
            print(report)
            print("--------------------------------------------------")
        

if __name__ == "__main__":
    match_id_subset = [1]
    run_picker_agent(match_id_subset)