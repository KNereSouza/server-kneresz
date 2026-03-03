"""Seed the database with demo data for development."""

import asyncio
import random

from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.models.comment import Comment
from app.models.post import Post
from app.models.slug_redirect import SlugRedirect
from app.models.user import User
from app.services.sanitizer import sanitize_markdown
from app.utils.slug import generate_slug

# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

ADMIN = {
    "github_id": settings.ADMIN_GITHUB_ID,
    "github_username": "kneresz",
    "avatar_id": 0,
}

COMMENTERS = [
    {"github_id": 100001, "github_username": "devnull", "avatar_id": 17},
    {"github_id": 100002, "github_username": "void_ptr", "avatar_id": 42},
    {"github_id": 100003, "github_username": "bitflip", "avatar_id": 91},
    {"github_id": 100004, "github_username": "segfault", "avatar_id": 63},
]

# ---------------------------------------------------------------------------
# Posts (published)
# ---------------------------------------------------------------------------

PUBLISHED_POSTS = [
    {
        "title": "Hello, World",
        "tags": ["meta"],
        "body": """\
Welcome. This is the first post on kneresz.com.

The site is intentionally minimal -- monospace font, grayscale palette, no
JavaScript analytics, no cookie banners. Content is what matters.

## Why build another blog?

Because every existing platform adds friction between thinking and publishing.
I wanted something I fully control: a FastAPI backend, a Next.js frontend, and
nothing else.

## What to expect

Posts about programming, tools, and the occasional tangent into typography or
keyboard hardware. No schedule, no newsletter, no engagement metrics.

```
$ echo "hello, world"
hello, world
```

That is all.
""",
    },
    {
        "title": "Async Python Is Not Magic",
        "tags": ["python", "async"],
        "body": """\
There is a common misconception that slapping `async` in front of a function
makes it faster. It does not. Understanding *why* requires knowing what the
event loop actually does.

## The event loop in 30 seconds

An event loop is a single-threaded scheduler. It keeps a queue of coroutines
and advances each one whenever it yields control (via `await`). If a coroutine
never yields, nothing else runs.

```python
import asyncio

async def block_everything():
    import time
    time.sleep(5)  # blocks the entire loop

async def main():
    await asyncio.gather(
        block_everything(),
        block_everything(),
    )
    # takes 10 seconds, not 5

asyncio.run(main())
```

The fix is to use `asyncio.sleep`, or offload CPU work to a thread pool via
`asyncio.to_thread`.

## When async helps

- **I/O-bound workloads**: database queries, HTTP calls, file reads
- **High concurrency**: handling thousands of connections with minimal threads
- **Streaming**: processing data as it arrives, not all at once

## When it does not

- **CPU-bound work**: number crunching, image processing, crypto
- **Simple scripts**: if you are not handling concurrent I/O, async adds
  complexity for zero benefit

The takeaway: async is a concurrency model, not a performance model. Know
the difference.
""",
    },
    {
        "title": "Terminal Workflows That Stuck",
        "tags": ["tools", "terminal"],
        "body": """\
I have tried dozens of terminal tools over the years. Most get uninstalled
within a week. Here are the ones that stayed.

## tmux

Session persistence is non-negotiable. If my SSH connection drops, my work
should still be there. Tmux gives me that, plus window splitting and session
naming.

Key bindings I actually use:

| Binding       | Action               |
|---------------|----------------------|
| `C-b c`       | new window           |
| `C-b ,`       | rename window        |
| `C-b %`       | vertical split       |
| `C-b "`       | horizontal split     |
| `C-b d`       | detach               |

## fzf

Fuzzy finding changes everything. `Ctrl+R` for history search, `Ctrl+T` for
file picking, `Alt+C` for directory jumping.

```bash
# find and edit a file
vim $(fzf --preview 'cat {}')
```

## ripgrep

Faster than grep, respects `.gitignore`, sane defaults. I aliased it to `rg`
years ago and never looked back.

```bash
rg "TODO|FIXME" --type py
```

## zoxide

`cd` with memory. `z project` jumps to whichever directory I visit most
often that matches "project". No more `cd ~/Code/work/projects/thing`.

The common thread: each tool does one thing well and composes with the rest.
""",
    },
    {
        "title": "The Case for Minimalist Design",
        "tags": ["design", "web"],
        "body": """\
Most websites are over-designed. Rounded corners, gradients, drop shadows,
animated transitions -- all applied by default, rarely justified by purpose.

## Decoration vs. communication

Every visual element on a page either helps the reader understand content or
it distracts from it. There is no neutral decoration. A subtle gradient still
takes up cognitive bandwidth.

This site uses:

- **One font** (monospace)
- **One color scale** (grayscale)
- **One layout** (single column)
- **Zero images** for decoration

The constraint is not a limitation. It is a filter. Anything that survives
this filter earns its place.

## Performance as design

Fewer assets means faster loads. No web fonts to fetch (monospace is a system
stack). No images to optimize. No JavaScript bundles for animation libraries.

```
Lighthouse score: 100 / 100 / 100 / 100
```

Performance is not an afterthought bolted on with lazy loading and CDNs. It
is the natural result of not adding things that do not need to be there.

## The reader's time

A reader who visits this site wants to read text. Everything that is not text
is a tax on their attention. Minimalism is not an aesthetic preference -- it
is respect for the reader's time.
""",
    },
    {
        "title": "Monospace Typography on the Web",
        "tags": ["typography", "web"],
        "body": """\
Proportional fonts dominate the web for good reason: they are easier to read
in long paragraphs. But monospace has its own advantages, especially for
technical content.

## Why monospace?

1. **Code and prose align.** No jarring font switches between paragraphs and
   code blocks.
2. **Columns line up.** Tables, ASCII art, and aligned comments render
   correctly without `<pre>` wrappers.
3. **Character counting is trivial.** Each character occupies the same width.
   Line lengths are predictable.

## The downsides

- Paragraphs consume more horizontal space
- Certain letter combinations (like "fi", "fl") lack ligatures
- Readers accustomed to proportional fonts may find it less comfortable

## Making it work

The key is generous line height and moderate line length. This site uses:

```css
body {
  font-family: 'Space Mono', monospace;
  line-height: 1.7;
}

.prose {
  max-width: 48rem;
}
```

At `line-height: 1.7`, monospace text breathes. At `max-width: 48rem`, lines
stay around 70-80 characters -- the sweet spot for readability.

Monospace is not for every site. But for a site about code and tools, it fits
like a glove.
""",
    },
    {
        "title": "Self-Hosting for Developers",
        "tags": ["infrastructure", "selfhost"],
        "body": """\
Self-hosting is not for everyone. But if you already manage servers for work,
running your own services is a small marginal cost with a large marginal
benefit.

## What I self-host

- **This blog** -- FastAPI + Next.js on a single VPS
- **Git mirrors** -- Gitea instance for backup, not collaboration
- **DNS** -- Pi-hole on the home network
- **Monitoring** -- Uptime Kuma for ping checks

## What I do not

- **Email** -- the deliverability problem is not worth solving
- **Chat** -- network effects make self-hosted chat useless
- **Anything with mobile sync** -- CalDAV/CardDAV are fragile

## The economics

A 2-core, 4GB VPS costs around $20/month. That runs all four services above
with headroom to spare. Compare that to:

| Service         | SaaS cost    |
|-----------------|-------------|
| Blog hosting    | $10-20/mo    |
| Git (private)   | $4-7/mo      |
| DNS filtering   | $3-5/mo      |
| Uptime monitor  | $7-15/mo     |

Self-hosting saves money *and* gives you full control. The trade-off is
maintenance time, but with Docker Compose and automatic updates, maintenance
is measured in minutes per month, not hours.

## The real reason

It is fun. Standing up a service from scratch, watching the logs, tweaking the
config. That is the part they do not put in the cost analysis.
""",
    },
    {
        "title": "Git Internals Worth Knowing",
        "tags": ["git", "tools"],
        "body": """\
You can use git productively without understanding its internals. But knowing
how it works underneath makes everything click.

## The object model

Git has four object types: **blob**, **tree**, **commit**, and **tag**. Every
object is identified by its SHA-1 hash.

```
blob   -- file contents (no filename, no metadata)
tree   -- directory listing (maps names to blob/tree hashes)
commit -- snapshot (points to a tree, parent commits, metadata)
tag    -- named pointer to a commit
```

A commit does not store diffs. It stores the full state of the repository at
that point. Diffs are computed on the fly by comparing trees.

## Branches are pointers

A branch is a file containing a 40-character hash. That is it.

```bash
$ cat .git/refs/heads/main
a1b2c3d4e5f6...
```

Creating a branch is writing 40 bytes to a file. Switching branches is
updating `HEAD` to point to a different ref. This is why branching in git
is instant.

## The reflog saves you

Every time `HEAD` moves, git records the previous position in the reflog.
Even after a hard reset, your commits are still there:

```bash
$ git reflog
a1b2c3d HEAD@{0}: reset: moving to HEAD~3
f7e8d9c HEAD@{1}: commit: add feature
...

$ git reset --hard f7e8d9c  # undo the reset
```

The reflog is your undo history. Entries expire after 90 days by default.

## Rebase is replay

`git rebase` does not move commits. It replays them. Each commit in the
range is cherry-picked onto the new base, creating new commits with new
hashes. The old commits still exist (in the reflog) until garbage collected.

Understanding this makes rebase conflicts less mysterious: you are resolving
the same conflicts you would get from cherry-picking each commit individually.
""",
    },
    {
        "title": "Keyboard-Driven Development",
        "tags": ["tools", "productivity"],
        "body": """\
The mouse is a general-purpose pointing device. For most development tasks,
the keyboard is faster.

## The argument

Every mouse interaction requires:

1. Moving your hand from the keyboard to the mouse
2. Visually locating the target
3. Moving the cursor to the target
4. Clicking
5. Moving your hand back to the keyboard

That is five steps for what could be one keystroke.

## Where it matters most

### Text editing

Vim motions (`w`, `b`, `ciw`, `dd`, `/%pattern`) are faster than
click-drag-select for almost every text manipulation. Even within VS Code,
the Vim extension pays for itself within a day.

### Window management

Tiling window managers (i3, sway, Hyprland) let you resize, move, and focus
windows without touching the mouse:

```
# i3 example
bindsym $mod+h focus left
bindsym $mod+l focus right
bindsym $mod+Return exec alacritty
bindsym $mod+Shift+q kill
```

### Browser navigation

Vimium (Chrome) or Tridactyl (Firefox) add keyboard navigation to the web.
`f` shows link hints, `/` searches, `J`/`K` switch tabs.

## The investment

Learning keyboard shortcuts is front-loaded effort with compounding returns.
You spend a few hours building muscle memory. Then you save seconds on every
interaction, thousands of times per day.

The math is overwhelmingly in favor of the keyboard.
""",
    },
]

DRAFT_POSTS = [
    {
        "title": "Thoughts on Container Orchestration",
        "tags": ["infrastructure", "docker"],
        "body": """\
Draft: comparing Docker Compose vs K3s for small-scale deployments.

## TODO

- benchmark resource usage
- compare deployment workflows
- test rolling updates
""",
    },
    {
        "title": "Writing a Markdown Parser from Scratch",
        "tags": ["python", "parsing"],
        "body": """\
Draft: step-by-step walkthrough of building a CommonMark parser.

## Outline

- tokenizer
- block-level parsing
- inline parsing
- AST to HTML
""",
    },
]

# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

COMMENTS = [
    ("Hello, World", "devnull", "nice clean setup. curious what you are using for deployment -- docker compose?"),
    ("Hello, World", "void_ptr", "refreshing to see a blog without a cookie consent banner covering half the screen"),
    ("Async Python Is Not Magic", "bitflip", "the time.sleep example is great -- seen this exact mistake in production more than once"),
    ("Async Python Is Not Magic", "segfault", "worth mentioning that asyncio.to_thread still has GIL limitations for CPU work. multiprocessing is the real escape hatch"),
    ("Async Python Is Not Magic", "devnull", "good writeup. i would add that httpx.AsyncClient is a much better example of where async shines vs requests"),
    ("Terminal Workflows That Stuck", "void_ptr", "no mention of lazygit? it changed how i interact with git entirely"),
    ("Terminal Workflows That Stuck", "bitflip", "zoxide is underrated. z is muscle memory at this point"),
    ("Terminal Workflows That Stuck", "segfault", "i replaced tmux with zellij recently. the default keybindings are much more intuitive"),
    ("The Case for Minimalist Design", "devnull", "this site is proof that the approach works. loads instantly even on bad connections"),
    ("The Case for Minimalist Design", "void_ptr", "counterpoint: some visual hierarchy (color, weight variation) helps scanability even in minimal designs"),
    ("Self-Hosting for Developers", "segfault", "agree on skipping email. spent a weekend setting up postfix once and the deliverability was still terrible"),
    ("Self-Hosting for Developers", "bitflip", "uptime kuma is great. switched from statping and never looked back"),
    ("Git Internals Worth Knowing", "devnull", "the reflog section alone is worth the read. saved me from a bad rebase last week"),
    ("Git Internals Worth Knowing", "void_ptr", "would love a follow-up on git pack files and how delta compression works"),
    ("Keyboard-Driven Development", "segfault", "been using vimium for years. the f key for link hints is the single biggest browser productivity gain"),
    ("Keyboard-Driven Development", "bitflip", "tiling WMs are life-changing but the learning curve is steep. took me a solid week to stop reaching for the mouse"),
    ("Keyboard-Driven Development", "devnull", "worth noting that not everyone can use keyboard-only workflows -- accessibility matters"),
]

# ---------------------------------------------------------------------------
# Slug redirects (simulate renamed posts)
# ---------------------------------------------------------------------------

SLUG_REDIRECTS = [
    ("hello", "Hello, World"),  # old slug -> post title
    ("async-python", "Async Python Is Not Magic"),
]


async def seed() -> None:
    async with async_session() as session:
        # Idempotency check
        existing = await session.execute(
            select(User).where(User.github_id == settings.ADMIN_GITHUB_ID)
        )
        if existing.scalar_one_or_none():
            print("seed: admin user already exists, skipping")
            return

        # -- Users ------------------------------------------------------------
        print("seed: creating users...")
        admin = User(**ADMIN)
        session.add(admin)
        await session.flush()

        commenter_map: dict[str, User] = {}
        for data in COMMENTERS:
            u = User(**data)
            session.add(u)
            commenter_map[data["github_username"]] = u
        await session.flush()

        # -- Published posts --------------------------------------------------
        print("seed: creating published posts...")
        post_map: dict[str, Post] = {}
        for i, data in enumerate(PUBLISHED_POSTS):
            post = Post(
                title=data["title"],
                slug=generate_slug(data["title"]),
                body=sanitize_markdown(data["body"]),
                tags=data["tags"],
                status="published",
            )
            session.add(post)
            post_map[data["title"]] = post
        await session.flush()

        # -- Draft posts ------------------------------------------------------
        print("seed: creating draft posts...")
        for data in DRAFT_POSTS:
            post = Post(
                title=data["title"],
                slug=generate_slug(data["title"]),
                body=sanitize_markdown(data["body"]),
                tags=data["tags"],
                status="draft",
            )
            session.add(post)
        await session.flush()

        # -- Comments ---------------------------------------------------------
        print(f"seed: creating {len(COMMENTS)} comments...")
        for post_title, username, body in COMMENTS:
            comment = Comment(
                post_id=post_map[post_title].id,
                user_id=commenter_map[username].id,
                body=sanitize_markdown(body),
            )
            session.add(comment)
        await session.flush()

        # -- Slug redirects ---------------------------------------------------
        print("seed: creating slug redirects...")
        for old_slug, post_title in SLUG_REDIRECTS:
            redirect = SlugRedirect(
                old_slug=old_slug,
                post_id=post_map[post_title].id,
            )
            session.add(redirect)

        await session.commit()
        print("seed: done")


if __name__ == "__main__":
    asyncio.run(seed())
