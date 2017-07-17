from flask import Flask, render_template
from flask import request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CategoryItem, User
import cgi

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"

engine = create_engine('sqlite:///catalogitems.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

session = DBSession()
app = Flask(__name__)


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current login state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps(
            'Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets(
            'client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'),
            200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id
    login_session['access_token'] = access_token

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']

    if(getUserID(login_session['email']) == None):
        createUser(login_session)
        user_id = getUserID(login_session['email'])
    else:
        user_id = getUserID(login_session['email'])

    login_session['user_id'] = user_id
    print 'user id in the session: ' + str(login_session['user_id'])

    output += ' " style = "width: 300px; height: 300px;border-radius: 150px; -webkit-border-radius: 150px; -moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(
        email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session.get('username')

    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    print url
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result

    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps(
            'Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/catalog/<int:category_id>/<int:category_item>/JSON')
def catalogItemJSON(category_id, category_item):
    result = session.query(CategoryItem).filter_by(
        category_id=category_id, id=category_item).one()
    return jsonify(CategoryItem=result.serialize)


@app.route('/catalog/JSON')
def catalogJSON():
    result = session.query(Category).all()
    return jsonify(Categories=[r.serialize for r in result])


@app.route('/')
@app.route('/catalog')
def showCatalogCategories():
    categories = session.query(Category).order_by(asc(Category.name))
    return render_template('catalog.html', categories=categories)


@app.route('/catalog/<int:category_id>/items')
def showCatalogCategoryItems(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(CategoryItem).filter_by(
        category_id=category.id)
    return render_template('catalogItems.html', category=category, items=items)


@app.route('/catalog/add', methods=['GET', 'POST'])
def catalogCategoryAdd():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCateogory = Category(name=request.form['name'])
        session.add(newCateogory)
        session.commit()
        flash('New Category Created!')
        return redirect(url_for('showCatalogCategories'))
    else:
        return render_template('addCatalogCategory.html')


@app.route('/catalog/<int:category_id>/<string:category_item>/desc', methods=['GET'])
def showCatalogCategoryItemsItem(category_id, category_item):
    result = session.query(CategoryItem).filter_by(
        category_id=category_id, id=category_item).one()
    print result
    print result.name
    return render_template('descCatalogItem.html', category_id=category_id, itemname=result.name, itemdesc=result.description)


@app.route('/catalog/<int:category_id>/add', methods=['GET', 'POST'])
def showCatalogCategoryItemsItemAdd(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    result = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        newItem = CategoryItem(name=request.form['name'], description=request.form['description'],
                               category_id=category_id, user_id=login_session['user_id'])
        if newItem.user_id != login_session['user_id']:
            return "<script>function myfunction(){alert('Not authorized to access');}</script><body onload='myfunction()'>"

        session.add(newItem)
        session.commit()
        flash('New Menu Item Created!')
        return redirect(url_for('showCatalogCategoryItems', category_id=category_id))
    else:
        return render_template('addCatalogItem.html', category_id=category_id, resultname=result.name)


@app.route('/catalog/<int:category_id>/<int:category_item>/edit', methods=['GET', 'POST'])
def showCatalogCategoryItemsItemEdit(category_id, category_item):
    if 'username' not in login_session:
        return redirect('/login')
    result = session.query(CategoryItem).filter_by(
        category_id=category_id, id=category_item).one()
    if result.user_id != login_session['user_id']:
        return "<script>function myfunction(){alert('Not authorized to access');}</script><body onload='myfunction()'>"
    if request.method == 'POST':
        print result.name
        result.name = request.form['name']
        result.description = request.form['description']

        print 'new:', result.name
        session.add(result)
        session.commit()
        flash('Menu Item edited!')
        return redirect(url_for('showCatalogCategoryItems', category_id=category_id))
    else:
        return render_template('editCatalogItem.html', category_id=category_id, category_item=category_item, item=result, itemname=result.name, itemdesc=result.description)

    return 'edit category item'


@app.route('/catalog/<int:category_id>/<int:category_item>/delete', methods=['GET', 'POST'])
def showCatalogCategoryItemsItemDelete(category_id, category_item):
    if 'username' not in login_session:
        return redirect('/login')
    result = session.query(CategoryItem).filter_by(
        category_id=category_id, id=category_item).one()
    if result.user_id != login_session['user_id']:
        return "<script>function myfunction(){alert('Not authorized to access');}</script><body onload='myfunction()'>"

    if request.method == 'POST':
        session.delete(result)
        session.commit()
        flash('Item Deleted!')
        return redirect(url_for('showCatalogCategoryItems', category_id=category_id))
    else:
        return render_template('deleteCatalogItem.html', category_id=category_id, category_item=category_item, item=result)


if __name__ == '__main__':
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
