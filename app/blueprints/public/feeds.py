from datetime import datetime, timezone
from flask import Response, render_template, request, url_for
from feedgen.feed import FeedGenerator

from app.models import Post, Gallery, TourDate
from . import bp


@bp.get("/feed.xml")
def feed():
    fg = FeedGenerator()
    fg.title("The Grog Blossoms — Ship's Log")
    fg.link(href=url_for("public.home", _external=True), rel="alternate")
    fg.link(href=url_for("public.feed", _external=True), rel="self")
    fg.description("Dispatches from the Quarterdeck.")
    fg.language("en")
    posts = (Post.query
             .filter(Post.published_at.isnot(None))
             .filter(Post.published_at <= datetime.utcnow())
             .order_by(Post.published_at.desc()).limit(50).all())
    for p in posts:
        fe = fg.add_entry()
        fe.id(url_for("public.log_detail", slug=p.slug, _external=True))
        fe.link(href=url_for("public.log_detail", slug=p.slug, _external=True))
        fe.title(p.title)
        fe.description(p.excerpt or "")
        fe.pubDate(p.published_at.replace(tzinfo=timezone.utc))
    return Response(fg.rss_str(pretty=True), mimetype="application/rss+xml")


@bp.get("/sitemap.xml")
def sitemap():
    urls = [
        url_for("public.home", _external=True),
        url_for("public.log_index", _external=True),
        url_for("public.manifest", _external=True),
        url_for("public.crew", _external=True),
        url_for("public.booty", _external=True),
        url_for("public.gallery_index", _external=True),
        url_for("public.crows_nest", _external=True),
    ]
    for p in Post.query.filter(Post.published_at.isnot(None)).all():
        if p.is_live():
            urls.append(url_for("public.log_detail", slug=p.slug, _external=True))
    for g in Gallery.query.all():
        urls.append(url_for("public.gallery_detail", slug=g.slug, _external=True))
    body = render_template("public/sitemap.xml", urls=urls)
    return Response(body, mimetype="application/xml")


@bp.get("/robots.txt")
def robots():
    return Response(render_template("public/robots.txt",
                                    sitemap_url=url_for("public.sitemap", _external=True)),
                    mimetype="text/plain")
