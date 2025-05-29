import os
import dotenv

dotenv.load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
POSTGRES_URL = os.getenv("POSTGRES_URL")


HELP_ARGS = """
<b>🛠️ Command Arguments Guide</b>

Most commands support additional arguments to customize behavior.

<b>🌐 Widget Language</b>

Widgets support three languages: English (default), Russian, and Uzbek.

To change the language, pass <code>en</code>, <code>ru</code>, or `uz` as an argument.

Examples:
<code>/calendar ru</code> — Show calendar in Russian  
<code>/calendar uz</code> — Show calendar in Uzbek

<b>📑 Pagination Settings</b>

You can control how many items appear per page and per row.

Format:
<blockquote>/pages [language] &lt;per_page&gt; &lt;per_row&gt;</blockquote>

Examples:
<code>/pages 9 3</code> —- 9 items per page, 3 items per row  
<code>/pages ru 7 2</code> -— Russian UI, 7 items per page, 2 items per row

Note:
<code>per_page</code> must be between 1 and 94.
<code>per_row</code> must be between 1 and 8.


⌚ <b>Time Selector Type</b>

Choose between two time selector styles: <b>Grid</b> and <b>Modern</b>.

Examples:
<code>/time grid</code> — Show Grid-style time selector  
<code>/time modern</code> — Show Modern-style time selector
"""
