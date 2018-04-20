import unittest
from movie2 import *

class TestAccess(unittest.TestCase):
	def testCSVRead(self):
		movie_list = []
		with open('movies2.csv') as csvDataFile:
			csvreader = csv.reader(csvDataFile)
			next(csvreader, None)
			for title in csvreader:
				movie = title[1]
				genre = title[2]
				title = movie.split('(')[:-1]
				movie_list.extend(title)

		self.assertIn(('My Favorite Year '), movie_list)
		self.assertEqual(movie_list[-1], 'Manhattan ')

	def testnytAPI(self):
		movie_review = []
		for movie in movie_list:
			try:
				movie_review.append(nyt_data(movie))
			except:
				pass

		self.assertEqual(movie_review[0]['status'], 'OK')

	def testOMDbAPI(self):
		movie_data = []
		for movie in movie_list:
			omdb = get_OMDBd_data(movie)
			if omdb["Response"]=="True":
				movie_data.append(OMDB(omdb))

		self.assertEqual(len(movie_data), 763)
s

class TestDBStorage(unittest.TestCase):
	def testMovies(self):
		conn = sqlite.connect(DBNAME)
		cur = conn.cursor()
		statement = 'SELECT Title FROM Movies'
		results = cur.execute(statement)
		results_list = results.fetchall()

		self.assertEqual(results_list[0], ('Toy Story',))
		self.assertIn(('Babe',), results_list)

	def testRatings(self):
		conn = sqlite.connect(DBNAME)
		cur = conn.cursor()
		statement = 'SELECT Rating FROM Ratings'
		results = cur.execute(statement)
		results_list = results.fetchall()

		self.assertEqual(len(results_list), 5)
		self.assertEqual(results_list[2], ('PG-13',))

	def testReviews(self):
		conn = sqlite.connect(DBNAME)
		cur = conn.cursor()
		statement = 'SELECT Review FROM Reviews'
		results = cur.execute(statement)
		results_list = results.fetchall()

		self.assertEqual(len(results_list), 762)
		self.assertIn(('No review',), results_list)

class TestProcessing(unittest.TestCase):
	def testNumMoviesByGenreData(self):
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

		self.assertEqual(genres['Comedy'], 237)
		self.assertEqual(len(genres), 21)

	def testRatingChartData(self):
		rating_lst = []
		count = []
		for x in rating():
			rating_lst.append(x[0])
		for x in rating():
			count.append(x[1])

		self.assertIn('G', rating_lst)
		self.assertIn(35, count)
		self.assertEqual(len(count), len(rating_lst))

	def testreviewscloudData(self):
		conn = sqlite.connect(DBNAME)
		cur = conn.cursor()
		statement = 'SELECT Review FROM Reviews'
		cur.execute(statement)
		text = ''
		for row in cur:
			text += row[0]

		self.assertEqual(len(text), 59561)
		self.assertIn('including best picture', text)

	def testreleaseyeardata(self):
		years_list = []
		number_movies = []
		for year in sorted_year():
			years_list.append(year[0])
			for movie in sorted_year():
				number_movies.append(movie[1])


		self.assertEqual(len(years_list), 80)
		self.assertEqual(len(number_movies), 6400)

unittest.main()
