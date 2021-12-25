#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json, sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from forms import *
from flask_moment import Moment
from flask_wtf import Form
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Show(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    venue_id = db.Column(db.ForeignKey('venue.id'), nullable=False)
    artist_id = db.Column(db.ForeignKey('artist.id'),nullable=False)
    start_time = db.Column('start_time', db.DateTime(), nullable=False)
    artist = db.relationship("Artist", back_populates="venues")
    venue = db.relationship("Venue", back_populates="artists")

class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(), nullable=False)
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String())
    artists = db.relationship('Show', back_populates='venue')

class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120), nullable=False)
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500), nullable=False)
    website_link = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String())
    venues = db.relationship('Show', back_populates='artist')


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  venues = Venue.query.group_by('id','name','state').all()
  data = []
  if len(venues) > 0:
    for idx, venue in enumerate(venues):
      if idx == 0:
        elem = {
          "city": venue.city,
          "state": venue.state,
          "venues": [{
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_show": 0
          }]
        }
      else:
        if venue.city == venues[idx-1].city:
          elem["venues"].append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_show": Show.query.filter(Show.venue_id == venue.id, Show.start_time >= datetime.now())
          })
        else:
          data.append(elem)
          elem = {
            "city": venue.city,
            "state": venue.state,
            "venues": [{
              "id": venue.id,
              "name": venue.name,
              "num_upcoming_show": Show.query.filter(Show.venue_id == venue.id, Show.start_time < datetime.now())
            }]
          }
    data.append(elem)
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  name = request.form['search_term']
  response = {
    "count": Venue.query.filter(Venue.name.ilike(f"%{name}%")).count(),
    "data": Venue.query.filter(Venue.name.ilike(f"%{name}%")).all()
  } 

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.filter_by(id=venue_id).first()
  past_shows = []
  shows_data = Show.query.filter(Show.venue_id == venue.id, Show.start_time < datetime.now()).all()
  data = []
  for show in shows_data:
    past_shows.append({
      "artist_id": show.artist_id,
      "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
      "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
      "start_time": show.start_time
    })
  upcoming_shows = []
  shows_data = Show.query.filter(Show.venue_id == venue.id, Show.start_time >= datetime.now()).all()
  data = []
  for show in shows_data:
    upcoming_shows.append({
      "artist_id": show.venue_id,
      "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
      "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
      "start_time": show.start_time
    })
  data={
    "id": venue.id,
    "address": venue.address,
    "name": venue.name,
    "genres": venue.genres.replace('"', "").replace("{", "").replace("}","").replace("[", "").replace("]","").split(","),
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows, #Artist.query.filter_by(id=artist_id).all(),
    "upcoming_shows": upcoming_shows,
    "past_shows_count": Show.query.filter(Show.venue_id == venue.id, Show.start_time < datetime.now()).count(),
    "upcoming_shows_count": Show.query.filter(Show.venue_id == venue.id, Show.start_time >= datetime.now()).count(),
  }
  print(data)
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form)
  error = False
  try:
    venue = Venue(name=form.name.data, city=form.city.data, state=form.state.data, address=form.address.data, phone=form.phone.data, genres=form.genres.data, facebook_link=form.facebook_link.data, website=form.website.data, image_link=form.image_link.data, seeking_talent=form.seeking_talent.data, seeking_description=form.seeking_description.data)
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Venue ' + venue.name + ' could not be listed.')
  finally:
    db.session.close()
    flash('Venue ' + venue.name + ' was successfully listed!')
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  success = True
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
    success=False
  finally:
    db.session.close()
  return jsonify({ 'success': success })

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.with_entities(Artist.id, Artist.name).order_by(Artist.name).all()
  print(data)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  name = request.form['search_term']
  response = {
    "count": Artist.query.filter(Artist.name.ilike(f"%{name}%")).count(),
    "data": Artist.query.filter(Artist.name.ilike(f"%{name}%")).all()
  } 
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.filter_by(id=artist_id).first()
  past_shows = []
  shows_data = Show.query.filter(Show.artist_id == artist.id, Show.start_time < datetime.now()).all()
  data = []
  for show in shows_data:
    past_shows.append({
      "venue_id": show.venue_id,
      "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
      "venue_image_link": Venue.query.filter_by(id=show.venue_id).first().image_link,
      "start_time": show.start_time
    })
  upcoming_shows = []
  shows_data = Show.query.filter(Show.artist_id == artist.id, Show.start_time >= datetime.now()).all()
  data = []
  for show in shows_data:
    upcoming_shows.append({
      "venue_id": show.venue_id,
      "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
      "venue_image_link": Venue.query.filter_by(id=show.venue_id).first().image_link,
      "start_time": show.start_time
    })
  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres.replace('"', "").replace("{", "").replace("}","").replace("[", "").replace("]","").split(","),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows, #Artist.query.filter_by(id=artist_id).all(),
    "upcoming_shows": upcoming_shows,
    "past_shows_count": Show.query.filter(Show.artist_id == artist.id, Show.start_time < datetime.now()).count(),
    "upcoming_shows_count": Show.query.filter(Show.artist_id == artist.id, Show.start_time >= datetime.now()).count(),
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  data = Artist.query.filter_by(id=artist_id).first()
  form.name.data = data.name
  form.city.data = data.city
  form.state.data = data.state
  form.phone.data = data.phone
  form.genres.data = data.genres
  form.facebook_link.data = data.facebook_link
  form.website_link.data = data.website_link
  form.image_link.data = data.image_link
  form.seeking_venue.data = data.seeking_venue
  form.seeking_description.data = data.seeking_description
  
  artist = {
    "id": data.id,
    "name": data.name,
  }
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)
  artist = Artist.query.filter_by(id=artist_id).first()
  try:
    artist.name=form.name.data
    artist.city=form.city.data
    artist.state=form.state.data
    artist.phone=form.phone.data
    artist.genres=form.genres.data
    artist.facebook_link=form.facebook_link.data
    artist.website_link=form.website_link.data
    artist.image_link=form.image_link.data
    artist.seeking_venue=form.seeking_venue.data
    artist.seeking_description=form.seeking_description.data
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Artist ' + artist.name + ' could not be updated.')
  finally:
    flash('Artist ' + artist.name + ' was successfully updated!')
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  data = Venue.query.filter_by(id=venue_id).first()
  form.name.data = data.name
  form.address.data = data.address
  form.city.data = data.city
  form.state.data = data.state
  form.phone.data = data.phone
  form.genres.data = data.genres
  form.facebook_link.data = data.facebook_link
  form.website_link.data = data.website
  form.image_link.data = data.image_link
  form.seeking_talent.data = data.seeking_talent
  form.seeking_description.data = data.seeking_description
  
  venue = {
    "id": data.id,
    "name": data.name,
  }
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form)
  venue = Venue.query.filter_by(id=venue_id).first()
  try:
    venue.name=form.name.data
    venue.city=form.city.data
    venue.state=form.state.data
    venue.phone=form.phone.data
    venue.genres=form.genres.data
    venue.facebook_link=form.facebook_link.data
    venue.website_link=form.website_link.data
    venue.image_link=form.image_link.data
    venue.seeking_talent=form.seeking_talent.data
    venue.seeking_description=form.seeking_description.data
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Artist ' + venue.name + ' could not be updated.')
  finally:
    flash('Artist ' + venue.name + ' was successfully updated!')
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form)
  error = False
  try:
    artist = Artist(name=form.name.data, city=form.city.data, state=form.state.data, phone=form.phone.data, genres=form.genres.data, facebook_link=form.facebook_link.data, website_link=form.website_link.data, image_link=form.image_link.data, seeking_venue=form.seeking_venue.data, seeking_description=form.seeking_description.data)
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Artist ' + artist.name + ' could not be listed.')
  finally:
    flash('Artist ' + artist.name + ' was successfully listed!')
    db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows_data = Show.query.all()
  data = []
  for show in shows_data:
    data.append({
      "venue_id": show.venue_id,
      "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
      "artist_id": show.artist_id,
      "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
      "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
      "start_time": show.start_time
    })
  print(data)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form)
  error = False
  try:
    p = Venue.query.filter_by(id=form.venue_id.data).first()
    a = Artist.query.filter_by(id=form.artist_id.data).first()
    ass = Show(artist=a, venue=p, start_time=form.start_time.data)
    db.session.add(ass)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Show could not be listed.')
  finally:
    if error == False:
      flash('Show was successfully listed!')
    db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
