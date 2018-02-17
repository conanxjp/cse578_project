import json

BUSINESS_DATA_FILE = './' + \
                     'business.json'

SAVE_DATA_FILE = './example.json'


def build_review_businesses():
    """Creates a json object taking review ids to the business id of their
    subject.
    """
    restaurants = list()

    f = open(BUSINESS_DATA_FILE, 'r')
    for line in f:
        business_data = json.loads(line)
        category = business_data["categories"]
        if "Restaurants" in category \
                or "Food" in category\
                or "Chinese" in category:
            restaurant = dict()
            restaurant["business_id"] = business_data["business_id"]
            restaurant["name"] = business_data["name"]
            restaurant["categories"] = business_data["categories"]
            restaurants.append(restaurant)
    return restaurants


def saveJson(restaurants):
    # j = json.dumps([value for value in restaurants], indent=4)
    f = open(SAVE_DATA_FILE, 'w')
    for value in restaurants:
        f.write(json.dumps(value))
        f.write('\n')
    f.close()
    return


def preprocess():
    """Runs preprocessing over the yelp dataset"""
    restaurants = build_review_businesses()
    saveJson(restaurants)
    return


if __name__ == '__main__':
    preprocess()