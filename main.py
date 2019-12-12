# [START app]
import logging
import urllib, urlparse, json

from flask import Flask, request, abort
import jinja2
import os

app = Flask(__name__)
JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

#
# class Recipe to represent Spoonacular recipes
#
class Recipe():
    def __init__(self, info):
        self.title = info["title"]
        self.image = info["image"]
        self.usedIngredientCount = info["usedIngredientCount"]
        self.id = info["id"]

    def __str__(self):
        return self.title

## Utility functions you may want to use
def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)

def safeGet(url):
    try:
        return urllib.urlopen(url)
    except Exception as e:
        logging.error("got exception: " + str(e))
    return None


# import secret flickr key
import spoonacular_key

# invoke the Flicker REST api with given params
def spoonREST(baseurl = 'https://api.spoonacular.com/recipes/',
    method = 'findByIngredients',
    api_key = spoonacular_key.key,
    params={},
    printurl = True
    ):
    params['apiKey'] = api_key
    url = baseurl + method + "?" + urllib.urlencode(params)
    if printurl:
        logging.info(url)
    return safeGet(url)

#
# Get cooking instructions for the given recipe id
#
def getInstructions(recipe_id):
    logging.info(("getInstructions for " + str(recipe_id)))
    method = str(recipe_id) + "/information"
    rsp = spoonREST(method=method)
    if not rsp:
        logging.warn("no recipe")
        return ""
    requeststr = rsp.read()
    recipe = json.loads(requeststr)
    if "instructions" not in recipe:
        logging.warn("no instructions included")
        return ""  
    return recipe["instructions"]

#  getReceipes() uses the Spoonacular API to
# get recipies for a given set of ingrediants.
# If get_instructions is True, instructions will be 
# loaded as well.
def getRecipes(ingredients, get_instructions=True):

    ingredients_param = ""
    if isinstance(ingredients, list):
        for ingredient in ingredients:
            ingredients_param += ingredient
            ingredients_param += ","
        ingredients_param = ingredients_param[:-1]  # strip off last comma
    else:
        ingredients_param = ingredients

    params = {"ingredients": ingredients_param}
    rsp = spoonREST(params=params)
    if not rsp:
        print("no rsp")
        return []
    requeststr = rsp.read()
    rspdata = json.loads(requeststr)
    recipes = [Recipe(info) for info in rspdata]
    logging.info("recipes loaded")
    if get_instructions:
        logging.info("get instructions")

        for recipe in recipes:
            recipe.instructions = getInstructions(recipe.id)
    return recipes

@app.route('/')
def show():
    logging.info("get recipes")
    if "ingredients"  in request.args:
        ingredients = request.args["ingredients"]
        logging.info("get recipes for tag: " + ingredients)

        recipes = getRecipes(ingredients)
        tag = "Recipes:"
        for recipe in recipes:
            logging.info("got recipe: " + recipe.title)
            logging.info("image: " + recipe.image)
        recipes.sort(key = lambda x: x.usedIngredientCount, reverse=True)
    else:
        tag = ""
        recipes = []

    template_values={"tagname": tag, "recipes": recipes}
    template = JINJA_ENVIRONMENT.get_template('cookme.html')
    s = template.render(template_values)

    return s



@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500
# [END app]
