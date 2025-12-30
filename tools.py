from dotenv import load_dotenv
from langchain_core.tools import Tool
from langchain_community.utilities import GoogleJobsAPIWrapper, GoogleSerperAPIWrapper

load_dotenv(override=True)

serpersearch = GoogleSerperAPIWrapper()
jobsearch = GoogleJobsAPIWrapper()


#async def playwright_tools():
#    playwright = await async_playwright().start()
#    browser = await playwright.chromium.launch(headless=True)
#    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
#   return toolkit.get_tools(), browser, playwright

async def other_tools():

    web_tool = Tool(
        name="Serper_Search",
        func=serpersearch.run,
        description="Use this tool to do web search."
    )

    job_tool = Tool(
        name="Job_Search_Tool",
        func=jobsearch.run,
        description="Use this tool to do job search."
    )

    return [web_tool, job_tool]

