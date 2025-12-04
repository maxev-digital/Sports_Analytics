# backend/ml/dfs/scrapers/fliff.py
from . import get_browser

async def scrape_fliff():
    browser = await get_browser()
    page = await browser.new_page()
    await page.goto("https://fliff.app/prop-bets")
    await page.wait_for_selector("[data-testid='prop-card']", timeout=30000)

    plays = await page.eval_on_selector_all("[data-testid='prop-card']", """
        cards => cards.map(card => ({
            player_name: card.querySelector('.player-name')?.innerText,
            stat_type: card.querySelector('.stat-type')?.innerText,
            line: parseFloat(card.querySelector('.line')?.innerText),
            direction: card.innerText.includes('Over') ? 'Higher' : 'Lower',
            site: "Fliff"
        }))
    """)

    await browser.close()
    return plays
