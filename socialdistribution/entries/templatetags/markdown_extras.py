from django import template
from django.utils.safestring import mark_safe
import commonmark

register = template.Library()

@register.filter(name='render_markdown')
def render_markdown(text):
    """
    Converts markdown text to HTML using CommonMark
    """
    if not text:
        return ''
    
    parser = commonmark.Parser()
    renderer = commonmark.HtmlRenderer()
    ast = parser.parse(text)
    html = renderer.render(ast)
    
    return mark_safe(html)