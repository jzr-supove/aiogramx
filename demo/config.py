import os
import dotenv

dotenv.load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

HELP_ARGS = """
<b>🛠️ Command Arguments Guide</b>

Most commands support additional arguments to customize behavior.

<b>🌐 Widget Language</b>

Widgets support three languages: English (default), Russian, and Uzbek.

To change the language, pass <code>en</code>, <code>ru</code>, or <code>uz</code> as an argument.

Examples:
<code>/calendar ru</code> — Show calendar in Russian  
<code>/calendar uz</code> — Show calendar in Uzbek

<b>📑 Pagination Settings</b>

You can control how many items appear per page and per row.

Format:
<blockquote>/pages [language] &lt;per_page&gt; &lt;per_row&gt;</blockquote>

Examples:
<code>/pages 9 3</code> — 9 items per page, 3 items per row
<code>/pages ru 7 2</code> — Russian UI, 7 items per page, 2 items per row

Note:
<code>per_page</code> must be between 1 and 94.
<code>per_row</code> must be between 1 and 8.


⌚ <b>Time Selector Settings</b>

Choose between two time selector styles: <b>Grid</b> and <b>Modern</b>.

Options:
- <b>modern</b> - Shows Modern-style time selector (default)
- <b>grid</b> - Shows Grid-style time selector
- <b>carry_over</b> - Minute overflows/underflows auto-adjust the hour
- <b>future_only</b> - Only allows selecting future times

<b>Usage examples:</b>
<code>/time grid</code> — Show Grid-style time selector
<code>/time modern</code> — Show Modern-style time selector
<code>/time ru carry_over future_only</code> - Modern-style selector with Russian UI, minute overflow auto-adjust hour, and restricts to future times only 
"""
