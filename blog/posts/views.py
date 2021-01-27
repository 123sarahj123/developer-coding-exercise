from django.http import HttpResponse 
from django.shortcuts import render
from django.contrib.staticfiles.utils import get_files
from django.contrib.staticfiles.storage import StaticFilesStorage
from django.conf import settings
import logging

import markdown
import codecs as co
import os
import re
from pathlib import Path
from collections import Counter

# Feel free to move this to a new file if you are carrying out the 'tags' calculation there
stopWords = [
    "#", "##", "a", "about", "above", "after", "again", "against", "all", "am",
    "an", "and", "any", "are", "aren't", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "can't", "cannot",
    "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't",
    "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's",
    "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how",
    "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't",
    "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that",
    "that's", "the", "their", "theirs", "them", "themselves", "then", "there", "there's",
    "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through",
    "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll",
    "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", "where",
    "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't",
    "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves"
]



def post(request, slug):
    """
        Checks to slug to ensure it is valid, and then fetches the corresponding md file
        and renders it as html. It will also append the top five tags of the blog post. 

        Should have set up a template for this. 

    """
    if checkSlug(slug) == True:
        blogContentsHTML, topFiveTags = getBlogContents(slug)

        #turn topFiveTags into HTML
        extractedTags = []
        for tag in topFiveTags:
            extractedTags.append(tag[0])

        topFiveTagsHtml = '<h2>Tags</h2>' + '<h3>' + str(extractedTags) + '</h3'

        return HttpResponse(blogContentsHTML + topFiveTagsHtml)
    else:
        return HttpResponse("<h1>ERROR: Could not find what you were looking for.</h1>")


def posts(request):
    """
        Displays list of blog post names from assets/posts as hyperlinks
        Sorry - the hyperlinks don't go anywhere!

    """
    blogPostsNameList = getFormattedBlogNames() 
    context = {
        'posts' : blogPostsNameList
    }
    return render(request, 'posts/home.html', context)



#-------------------------------------------------------------
## SARAH'S HELPER METHODS
#-------------------------------------------------------------


def checkSlug(slug):
    """
        Checks the slug from the URL against the available slugs (i.e. name of the markdown file in assets/posts without the extenstion)
        Returns a boolean
    """
    bExists = False
    existingSlugs = getUnformattedBlogNamesAsSlugs()
    if slug in existingSlugs:
        bExists = True
    return bExists


def getFormattedBlogNames():
    """
        Returns a list of the blog names found under assets/posts.
        Each blog name has been taken taken from the name of the markdown file,
        so the hyphens and extension have been removed, as well as capitalizing 
        each word in the blog name. 

        If I had more time to figure out Django, I would have dynamiccaly pulled the list of blog names out of the markdown files. 

    """
    path=settings.STATICFILE_DIR  # insert the path to your directory
    assetBlogList =os.listdir(path)
    blogList = []
    for blogName in assetBlogList:
        strippedBlogName = blogName.replace("-", " ") #remove hyphens
        removedExtensionBlogName = strippedBlogName.replace(".md", "") #remove extension
        blogList.append(removedExtensionBlogName.title()) #capitalize start of each word
    print(blogList)    
    return blogList


def getUnformattedBlogNamesAsSlugs():
    """
        Returns a list of the blognames/slugs found under assets/blog
        without the .md extension. 
    """
    path=settings.STATICFILE_DIR  # insert the path to your directory
    assetBlogList =os.listdir(path)
    slugList = []
    for blogName in assetBlogList:
        removedExtensionBlogName = blogName.replace(".md", "") #remove extension
        slugList.append(removedExtensionBlogName) 
    return slugList


def getBlogContents(slug):
    """
        Takes the slug, finds its corresponding markdown file in assets\posts, and converts the markdown file
        into an htmlFile.

        Due to rushing and convenience, I also added the functionality here to pull out the top five tags found in the article.

        Returns converted HTML file, and a list of the top five tags. 
    """
    slug += '.md' #readd the extension to the slug
    path = os.path.join(settings.STATICFILE_DIR, slug)
    markdownFile = co.open(path, mode="r", encoding="utf-8")
    readMarkdownFile = markdownFile.read()

    # start converting to html file
    htmlFile = markdown.markdown(readMarkdownFile)
    out = co.open("out.html", "w", encoding="utf-8", errors="xmlcharrefreplace")
    out.write(htmlFile)
    topFiveTags = getTopFiveTags(readMarkdownFile) # get the top 5 tags

    return htmlFile, topFiveTags



def getTopFiveTags(markdownFile):
    """
        Takes article of a blog, and list of stop words, and returns the 5 most common words
        in the article. It will take the 5 most common words from the article ONLY (not the title, author, etc).
        Returns the 5 most common words as a list of tuples {key=word, value=count}

        This algorithm currently has some flaws.
        1) Should have used regex or another way of stripped all of the unwanted chars/symbols
        2) Will include some symbols in the count like '' and ' ' that I didn't have time to figure out.
        3)
    """

    wordCount = {}

    strippedStopWords = []
    #simplify stopwords
    for stopWord in stopWords:
        if "'" in stopWord:
            stopWord = stopWord.replace("'", "") #apostrophes seem to be the only threat
        strippedStopWords.append(stopWord)

    #simplify blog post
    strippedBlogContent = []
    markdownFile = re.sub('[0-9]+', '', markdownFile) #remove numbers from the string
    for word in markdownFile.lower().split(' '):
        word = word.replace("'", "") 
        word = word.replace("."," ")
        word = word.replace(",","")
        word = word.replace("*","")
        word = word.replace(":","")
        word = word.replace("\"","")
        word = word.replace("!","")
        word = word.replace(")","")
        word = word.replace("(","")
        word = word.replace("===","")
        word = word.replace(":","")
        word = word.replace("/","")    
        word = word.replace("#","")
        word = word.replace("-"," ")
        word = word.replace("]","")
        word = word.replace("["," ")
        word = word.replace("''","")
        word = word.replace("%","")
        word = word.replace("\n","")
        
        if word not in strippedStopWords:
            if word not in wordCount:
                wordCount[word] = 1
            else:
                #increment the count
                wordCount[word] += 1   

    # Now to output the 5 most common words in the blog
    fiveMostCommonWords = []
    sortedValues = sorted(wordCount, key=lambda k:(wordCount[k], k) )

    x = range (len(sortedValues)-1, len(sortedValues) - 6, -1)
    for i in x:
        key = sortedValues[i]
        value = wordCount.get(sortedValues[i])
        fiveMostCommonWords.append((key, value))

    #this works, although I have now spent a bit too much time, and not sure I'll figure out how to get this into the HTML file tidily
    #this algorithm also isn't perfect (rushed it). It will return '' and ' ' in the count. 
    return fiveMostCommonWords 



# def getBlogPosts():
#     """
#     Contructs a dictionary of the blog posts where the slug (or name of the md file) is the key, and the value
#     is composed of another dictionary with the format of:
#     {
#         'Title': title
#         'Author': author
#         'Heading': the secondary heading preceded by '#'
#         'Content': body of article

#     }
        
#     """







