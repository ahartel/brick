import os
from waflib.Configure import conf

def configure(conf):
	pass

@conf
def write_cds_lib(self):
	cdslib = open('cds.lib','w')

	for key,value in self.env['CDS_LIBS'].iteritems():
		cdslib.write('DEFINE '+key+' '+value+"\n")

	cdslib.close()

@conf
def check_cds_libs(self,*k,**kw):
	self.env['CDS_LIBS'] = {}
	for key,value in kw.iteritems():
		if type(value) == type('str'):
			# DEFINE
			if os.path.isdir(value):
				libpath = self.path.find_dir(value)
				self.env['CDS_LIBS'][key] = libpath.abspath()
			else:
				self.fatal('Directory '+value+' not found.')
		elif type(value) == type([]):
			# INCLUDE
			# TODO: implement
			pass

	self.write_cds_lib()
