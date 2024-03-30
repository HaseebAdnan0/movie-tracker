from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, Column, URL
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests
import json

movie_access_token = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyNThjMDU1YWE3YmM4OGNiMzdiOWJmOWE5MTE1Mjk3ZCIsInN1YiI6IjY2MDc5ZTlmZjkxODNhMDE0YzQ3Mjc0OCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.vdOLpE3k9SBVJEqToq_RpiFoLl4Jhn-Hg99zW21ANjs"
movie_search_endpoint = "https://api.themoviedb.org/3/search/movie"
header = {"Authorization": f"Bearer {movie_access_token}"}

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///new-movies-collection.db"
db = SQLAlchemy(app)
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"


# CREATE DB
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), unique=True)
    year = db.Column(db.Integer)
    description = db.Column(db.String(5000))
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(500))
    img_url = db.Column(db.String(500))


# CREATE TABLE
with app.app_context():
    # Create table schema in the database
    db.create_all()


class RateMovieForm(FlaskForm):
    updated_rating = FloatField(f"Your Rating out of 10. e.g. 7.5")
    updated_review = StringField(f"Your Review")
    submit = SubmitField("Done")


class AddMovie(FlaskForm):
    title = StringField(f"Movie Title")
    submit = SubmitField("Add Movie")


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie_to_update = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie_to_update.rating = float(form.updated_rating.data)
        movie_to_update.review = form.updated_review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie_to_update, form=form)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovie()
    if form.validate_on_submit():
        title = form.title.data
        parameters = {
            "query": title,
        }
        response = requests.get(movie_search_endpoint, headers=header, params=parameters)
        response.raise_for_status()
        results = response.json()["results"]
        return render_template("select.html", results=results)
    return render_template("add.html", form=form)


@app.route("/find")
def find():
    id_to_search = request.args.get("id")
    if id_to_search != "":
        movie_details_endpoint = f"https://api.themoviedb.org/3/movie/{id_to_search}"
        response = requests.get(movie_details_endpoint, headers=header)
        response.raise_for_status()
        result = response.json()
        existing_movie = Movie.query.filter_by(title=result["title"]).first()
        if not existing_movie:
            new_movie = Movie(
                title=result["title"],
                img_url=f"{MOVIE_DB_IMAGE_URL}{result['poster_path']}",
                year=result['release_date'][0:4],
                description=result['overview']
            )
            db.session.add(new_movie)
            db.session.commit()
    return redirect(url_for('edit', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0")
