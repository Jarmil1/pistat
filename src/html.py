#! /usr/bin/python3

# generovani HTML

import func


def span(content, html_class='', style=''):
    return "<span class='%s' style='%s'>%s</span>" % (html_class, style, content)
    
    
def h2(content):
    return "<h2>%s</h2>\n" % content

    
def h1(content):
    return "<h1>%s</h1>\n" % content
    
    
def stylesheet(url):
    return "<link rel=\"stylesheet\" type=\"text/css\" href=\"%s\" />\n" % url
    
    
def p(content):    
    return "<p>%s</p>\n" % content

    
def a(url, text):
    return "<a href=\"%s\">%s</a>" % (url, text)
