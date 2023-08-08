import mysql.connector
import pathlib, os

# The Piwigo database has been loaded into the mysql server on localhost,
# to a database called 'piwiz'. Make some mysql calls to build a python
# representation of the album structure.

# A database connnection
con = mysql.connector.connect(user='alex', password='', host='localhost', database='piwiz')

# First some helper classes.
class Image:
	def __init__(self, image_id, path, filename, album=''):
		self.id = image_id
		self.path = path
		self.filename = filename
		self.album = album

class Album:
	def __init__(self, album_id, name, parent=None):
		self.id = album_id
		self.name = name
		self.parent = parent

class Tree:
	"""
	A hierarchical tree of albums, mapping album id to an album path
	"""
	def __init__(self):
		self.dct = {}  # dict of albums, {id: Album object}

	def add_album(self, album_id, name, parent_id):
		self.dct[album_id] = Album(album_id, name, parent_id)

	def path(self, album_id):
		if self.dct[album_id].parent:
			return self.path(self.dct[album_id].parent) + '/' + self.dct[album_id].name
		else:
			return self.dct[album_id].name

# Make a tree of the albums, so we have paths available
tree = Tree()
cursor = con.cursor()
cursor.execute('SELECT id, id_uppercat, name FROM categories')
for cat in cursor:
	idn, parent_id, name = cat
	tree.add_album(idn, name, parent_id)

# Go through the image-category table, make a dict {image_id: category_id}
cursor.execute('SELECT image_id, category_id FROM image_category')
im2cat = {}
for im in cursor:
	image_id, category_id = im
	im2cat[image_id] = category_id

# Go through the images, make a dict of Image objects with all the info. Voila!
cursor.execute('SELECT id, file, path FROM images')
images = {}
for im in cursor:
	idn, filename, path = im
	image = Image(image_id=idn, path=path, filename=filename, album=tree.path(im2cat[idn]))
	# print('Id: %d, Name: %s, Location: %s, Album: %s' % (image.id, image.filename, image.path, image.album))
	images[path.rsplit('/', 1)[1]] = image
print('\nDatabase has %d images in total' % len(images))

# Now go through the Piwigo zip files one by one, unzip and loop over the images
inpath = '/home/alexanbj/foto/'
outpath = '/media/alexanbj/alex_usb_2tb/migration/album/'
zipfiles = pathlib.Path(inpath).rglob('*.zip')
for zipfile in zipfiles:
	os.system('unzip %s -d /tmp/' % zipfile)
	image_files = [str(f) for f in pathlib.Path('/tmp/').rglob('*') if '.jp' in str(f).lower()]
	for im_file in image_files:
		try:
			im_obj = images[im_file.rsplit('/', 1)[1]]
			album = im_obj.album
			os.system('mkdir -p "%s%s"' % (outpath, album))
			os.system('mv %s "%s%s/%s"' % (im_file, outpath, album, im_obj.filename))
		except KeyError:
			os.system('mv %s %s' % (im_file, inpath))
