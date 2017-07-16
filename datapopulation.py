from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base, CategoryItem, User

engine = create_engine('sqlite:///catalogitems.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create dummy user
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

category1 = Category(name="Snowboarding")
session.add(category1)
session.commit()

categoryItem1 = CategoryItem(user_id=1, name="Snow shoes", description="snow shoes for snow!", category=category1)
session.add(categoryItem1)
session.commit()

categoryItem2 = CategoryItem(user_id=1, name="Snow glasses", description="snow glasses for snow!", category=category1)
session.add(categoryItem2)
session.commit()

categoryItem3 = CategoryItem(user_id=1, name="Snow gloves", description="snow gloves for snow!", category=category1)
session.add(categoryItem3)
session.commit()

category2 = Category(name="Baseball")
session.add(category2)
session.commit()

categoryItem1 = CategoryItem(user_id=1, name="Baseball shoes", description="baseball shoes for baseball!", category=category2)
session.add(categoryItem1)
session.commit()

categoryItem2 = CategoryItem(user_id=1, name="Baseball glasses", description="baseball glasses for baseball!", category=category2)
session.add(categoryItem2)
session.commit()


print "added category items!"