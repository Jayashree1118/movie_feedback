from flask import Flask, render_template, request, redirect, url_for, flash
import pymysql
import json
from flask import jsonify 

app = Flask(__name__)
app.secret_key = "your_secret_key"  # For flash messages

# RDS configuration
rds_host = 'database-1.crigwewwg7vt.us-east-1.rds.amazonaws.com'  # Replace with your RDS endpoint
rds_port = 3306  # Default MySQL port
db_username = 'admin'  # Replace with your database username
db_password = 'PASSWORD'  # Replace with your database password
db_name = 'movie_feedback'  # Replace with your database name

print(rds_host)

# Connect to the RDS MySQL database
def connect_to_rds():
    try:
        connection = pymysql.connect(
            host=rds_host,
            user=db_username,
            password=db_password,
            database=db_name,
            port=rds_port
        )
        print("Connected to the database!")
        return connection
    except pymysql.MySQLError as e:
        print(f"Error connecting to the database: {e}")
        return None

def getMovies():
    connection = connect_to_rds()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM movie")
            movies = cursor.fetchall()
            if movies:
                keys = ['id', 'title', 'description', 'total_review', 'avg_rating', 'image_url']
                json_data = []
                for item in movies:
                    movie_dict = dict(zip(keys, item))
                    # Map image_url correctly to Flask's /static/images/
                    if movie_dict['image_url']:
                        movie_dict['image_url'] = f"/static/image/{movie_dict['image_url']}"
                    json_data.append(movie_dict)
                return json_data
            return []
        except pymysql.MySQLError as e:
            print(f"Error fetching movies: {e}")
            return []
    return []


def getMovieData(movie_id):
    connection = connect_to_rds()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM movie WHERE id=%s", (movie_id,))
            movie = cursor.fetchone()
            if movie:
                keys = ['id', 'title', 'description', 'total_review', 'avg_rating', 'image_url']
                return dict(zip(keys, movie))
            return None
        except pymysql.MySQLError as e:
            print(f"Error fetching movie data: {e}")
            return None
    return None

def updateMovieData(movie_id, total_reviews, avg_rating):
    connection = connect_to_rds()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute('''UPDATE movie SET avg_rating = %s, total_review = %s WHERE id = %s''', 
                           (avg_rating, total_reviews, movie_id))
            connection.commit()
            return True
        except pymysql.MySQLError as e:
            print(f"Error updating movie data: {e}")
            return False
    return False

def addFeedback(name, email, feedback_text, rating, movie_name):
    connection = connect_to_rds()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute('''INSERT INTO feedback (movie, name, email, feedback, rating)
                              VALUES (%s, %s, %s, %s, %s)''', 
                              (movie_name, name, email, feedback_text, rating))
            connection.commit()
            return True
        except pymysql.MySQLError as e:
            print(f"Error adding feedback: {e}")
            return False
    return False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/movie')
def movies():
    movies = getMovies()
    return render_template('movie.html', data=movies)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        data = json.loads(request.data.decode('utf-8'))
        movie_id = data.get("id", "")
        movie_name = data.get("movie_name", "")
        name = data.get("name", "")
        email = data.get("email", "")
        feedback_text = data.get("feedback", "")
        rating = int(data.get("rating", 0))

        if addFeedback(name, email, feedback_text, rating, movie_name):
            movie_data = getMovieData(movie_id)
            if movie_data:
                avg_rating = movie_data["avg_rating"]
                total_reviews = movie_data["total_review"]

                new_avg_rating = ((avg_rating * total_reviews) + rating) / (total_reviews + 1)
                new_total_reviews = total_reviews + 1
                updateMovieData(movie_id, new_total_reviews, new_avg_rating)

        return render_template('thankyou.html')

    movie_name = request.args.get("name")
    return render_template('feedback.html', data=movie_name)

@app.route('/thank-you', methods=['GET', 'POST'])
def thank_you():
    return render_template('thankyou.html')

if __name__ == '__main__':
    app.run(debug=True)


