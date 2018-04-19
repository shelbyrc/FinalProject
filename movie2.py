from secrets2 import *
import requests
import json
import csv
import sqlite3 as sqlite
import plotly.plotly as py
import plotly.graph_objs as go
from wordcloud import WordCloud # `pip install wordcloud` from https://github.com/amueller/word_cloud
import matplotlib.pyplot as plt

DBNAME = 'movie.db'

CACHE_FNAME = 'movies.json'
try:
	cache_file = open(CACHE_FNAME, 'r')
	cache_contents = cache_file.read()
	CACHE_DICTION = json.loads(cache_contents)
	cache_file.close()

# if there was no file, no worries. There will be soon!
except:
	CACHE_DICTION = {}

# A helper function that accepts 2 parameters
# and returns a string that uniquely represents the request
# that could be made with this info (url + params)
def params_unique_combination(baseurl, params):
	alphabetized_keys = sorted(params.keys())
	res = []
	for k in alphabetized_keys:
		res.append("{}-{}".format(k, params[k]))
	return baseurl + "_".join(res)

# The main cache function: it will always return the result for this
# url+params combo. However, it will first look to see if we have already
# cached the result and, if so, return the result from cache.
# If we haven't cached the result, it will get a new one (and cache it)
def make_request_using_cache(baseurl, params={}, auth=None):
	unique_ident = params_unique_combination(baseurl,params)

	## first, look in the cache to see if we already have this data
	if unique_ident in CACHE_DICTION:
		#print("Getting cached data...")
		return CACHE_DICTION[unique_ident]

	## if not, fetch the data afresh, add it to the cache,
	## then write the cache to file
	else:
		#print("Making a request for new data...")
		# Make the request and cache the new data
		resp = requests.get(baseurl, params, auth=auth)
		CACHE_DICTION[unique_ident] = resp.text
		dumped_json_cache = json.dumps(CACHE_DICTION)
		fw = open(CACHE_FNAME,"w")
		fw.write(dumped_json_cache)
		fw.close() # Close the open file
		return CACHE_DICTION[unique_ident]

def init_db(db_name):
	conn = sqlite.connect(db_name)
	cur = conn.cursor()

	statement = '''
		DROP TABLE IF EXISTS 'Ratings';
	'''
	cur.execute(statement)

	statement = '''
		DROP TABLE IF EXISTS 'Movies';
	'''
	cur.execute(statement)

	statement = '''
		DROP TABLE IF EXISTS 'Reviews';
	'''
	cur.execute(statement)

	statement = '''
		CREATE TABLE 'Ratings' (
			'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
			'Rating' TEXT NOT NULL
		);
	'''
	cur.execute(statement)

	statement = '''
		CREATE TABLE 'Movies' (
			'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
			'Title' TEXT NOT NULL,
			'Year' TEXT,
			'RatingId' INTEGER,
			'ReleaseDate' TEXT,
			'Genre' TEXT,
			'Actors' TEXT
		);
	'''
	cur.execute(statement)

	statement = '''
		CREATE TABLE 'Reviews' (
			'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
			'Review' TEXT NOT NULL,
			'MovieTitle' TEXT
		);
	'''
	cur.execute(statement)
	conn.commit()
	conn.close()

movie_list = []
with open('movies2.csv') as csvDataFile:
	csvreader = csv.reader(csvDataFile)
	next(csvreader, None)
	for title in csvreader:
		movie = title[1]
		genre = title[2]
		title = movie.split('(')[:-1]
		movie_list.extend(title)

def insert_rating():
	conn = sqlite.connect(DBNAME)
	cur = conn.cursor()
	with open('rating.csv') as csvDataFile:
		csvreader = csv.reader(csvDataFile)
		next(csvreader, None)
		for rating in csvreader:
			rating = rating[0]
			statement = 'INSERT INTO Ratings'
			statement += ' VALUES (?,?)'
			insertion = (None,rating)
			cur.execute(statement,insertion)
		conn.commit()
		conn.close()

def get_OMDBd_data(title):
	response = make_request_using_cache('http://www.omdbapi.com', params = {'apikey': OMDb_api_key, 't': title })
	result = json.loads(response)
	return result

class OMDB():
	def __init__(self, data):
		self.title = data["Title"]
		self.year = data["Year"]
		self.rating = data["Rated"]
		self.release_date = data["Released"]
		self.actors = data["Actors"]
		self.genre = data["Genre"]

movie_data = []
for movie in movie_list:
	omdb = get_OMDBd_data(movie)
	if omdb["Response"]=="True":
		movie_data.append(OMDB(omdb))

def insert_movie_info():
	conn = sqlite.connect(DBNAME)
	cur = conn.cursor()
	for omdb_inst in movie_data:
		statement = 'SELECT Id from Ratings WHERE Rating=?'
		insertion = (omdb_inst.rating,)
		cur.execute(statement,insertion)
		try:
			rating_id = cur.fetchone()[0]
		except:
			rating_id = None

		statement = 'INSERT INTO Movies'
		statement += ' VALUES (?,?,?,?,?,?,?)'
		insertion = (None,omdb_inst.title,omdb_inst.year,rating_id,omdb_inst.release_date,omdb_inst.genre,omdb_inst.actors)
		cur.execute(statement,insertion)
	conn.commit()
	conn.close()

def nyt_data(title):
	response = make_request_using_cache('https://api.nytimes.com/svc/movies/v2/reviews/search.json', params = {'api-key': nyt_api, 'query': "\'{}\'".format(title.strip()) })
	result = json.loads(response)
	return result

movie_review = []
for movie in movie_list:
	try:
		movie_review.append(nyt_data(movie))
	except:
		pass

def insert_review():
	conn = sqlite.connect(DBNAME)
	cur = conn.cursor()
	for info in movie_review:
		if "results" in info:
			for review in info["results"]:
				if len(review["summary_short"]) == 0:
					reviews = "No review"
				else:
					reviews = review["summary_short"]
				title = review["display_title"]
				statement = 'INSERT INTO Reviews'
				statement += ' VALUES (?,?,?)'
				insertion = (None, reviews, title)
				cur.execute(statement,insertion)
				conn.commit()
	conn.close()

def sorted_year():
	conn = sqlite.connect(DBNAME)
	cur = conn.cursor()
	statement = 'SELECT ReleaseDate FROM Movies'
	cur.execute(statement)
	release_years = {}
	for row in cur:
		release_year = row[0].split()[-1]
		if release_year.isnumeric():
			if release_year not in release_years:
				release_years[release_year] = 1
			else:
				release_years[release_year] += 1
	sorted_years = sorted(release_years.items(), key = lambda x: x[0])
	conn.close()
	return sorted_years

def rating():
	conn = sqlite.connect(DBNAME)
	cur = conn.cursor()
	statement = 'SELECT Ratings.Rating, COUNT(*) FROM Ratings'
	statement += ' JOIN Movies ON Ratings.Id = Movies.RatingId'
	statement += ' GROUP BY Ratings.Rating'
	cur.execute(statement)
	results = cur.fetchall()
	return results

if __name__ == '__main__':
	init_db(DBNAME)
	insert_rating()
	insert_movie_info()
	insert_review()


	while True:
		response = input('Enter a command (ratings, release years, genres, or reviews), help, or exit to quit: ')
		if response != 'exit':
			if response.lower() == 'release years':
				years_list = []
				number_movies = []
				for year in sorted_year():
					years_list.append(year[0])
					for movie in sorted_year():
						number_movies.append(movie[1])

						data = [go.Bar(
						x=years_list,
						y=number_movies
				)]
				py.plot(data, filename='years-bar')
				continue

			if response.lower() == 'ratings':
				rating_lst = []
				count = []
				for x in rating():
					rating_lst.append(x[0])
				for x in rating():
					count.append(x[1])
				labels = rating_lst
				values = count
				trace = go.Pie(labels=labels, values=values)
				py.plot([trace], filename='rating_chart')
				continue

			if response.lower() == 'genres':
				conn = sqlite.connect(DBNAME)
				cur = conn.cursor()
				statement = 'SELECT Genre FROM Movies'
				cur.execute(statement)
				genres = {}
				for row in cur:
					genre = row[0].split(',')[0]
					if genre not in genres:
						genres[genre] = 1
					else:
						genres[genre] += 1

				data = [go.Bar(
					x=list(genres.values()),
					y=list(genres.keys()),
					orientation = 'h',
					marker = dict(
						color = 'rgba(246, 78, 139, 0.6)',
						)
				)]
				py.plot(data, filename='genres-bar')
				continue

			if response.lower() == 'reviews':
				conn = sqlite.connect(DBNAME)
				cur = conn.cursor()
				statement = 'SELECT Review FROM Reviews'
				cur.execute(statement)
				text = ''
				for row in cur:
					text += row[0]
				wordcloud = WordCloud().generate(text)
				plt.imshow(wordcloud, interpolation='bilinear')
				plt.axis("off")
				plt.savefig("reviews_cloud.png")
				print("See the word cloud in the file 'reviews_cloud.png'!")
				continue

			if response.lower() == 'help':
				print('''
					The 'ratings' command creates a pie chart of the percentages of ratings of all the movies.
					The 'release years' command creates a bar chart of the amount of movies released each year.
					The 'genres' command creates a horizontal bar chart of the amount of movies in each genre.
					The 'reviews' command creates a word cloud based on all the reviews.
				''')

			else:
				print('Please enter a valid command! ')

		if response.lower() == 'exit':
			print('Bye!')
			break
