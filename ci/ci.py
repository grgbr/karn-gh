#!/usr/bin/python

import sys
import os
import errno
import glob
import jenkins
import jinja2
import argparse as argp

class CiSecret:
	def get_from_plain_file(self, secret_path):
		with open(secret_path, 'r') as f:
			secret = f.read().strip(" \t\n")

		return secret


class Ci:
	server = None


	def __init__(self, url, user, passwd):
		self._server = jenkins.Jenkins(url, username=user,
		                               password=passwd)


	def list_branch_folders(self, config_dirpath, folder_prefix):
		folders = []

		if config_dirpath == None or not os.path.isdir(config_dirpath):
			raise IOError(errno.ENOENT, 'No such directory', config_dirpath)

		for f in glob.glob(os.path.join(config_dirpath, '*.config')):
			name, _ = os.path.splitext(os.path.basename(f))
			fold = self._server.get_job_name('{}{}'.format(folder_prefix,
			                                               name))
			if fold and \
			   self._server.get_job_info(fold)['_class'] == \
			   'org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject':
				folders.append(fold)

		return folders


	def list_branch_jobs(self, config_dirpath, folder_prefix):
		jobs = []

		for f in self.list_branch_folders(config_dirpath, folder_prefix):
			for j in self._server.get_job_info(f)['jobs']:
				if j['_class'] == \
				   'org.jenkinsci.plugins.workflow.job.WorkflowJob':
					jobs.append('{}/{}'.format(f, j['name']))

		return jobs


	def run_branch_jobs(self, config_dirpath, folder_prefix):
		if config_dirpath == None or not os.path.isdir(config_dirpath):
			raise IOError(errno.ENOENT, 'No such directory', config_dirpath)

		for j in self.list_branch_jobs(config_dirpath, folder_prefix):
			print('start running \'{}\' job'.format(j))
			self._server.build_job(j)


	def create_branch_folder(self, name, display, keepnr, uri, script_path,
	                         template_path):
		if name == None:
			raise Exception('Error: Invalid folder name: \'{}\''.format(name))

		if self._server.job_exists(name):
			raise Exception('Error: Branch folder already ' \
			                'exists: \'{}\''.format(name))

		if display == None:
			raise Exception('Error: Invalid branch folder display name: ' \
			                '\'{}\''.format(display))

		if keepnr <= 0:
			raise Exception('Invalid number of kept build jobs: ' \
			                '\'{}\''.format(keepnr))

		if uri == None:
			raise Exception('Error: Invalid branch folder git repository ' \
			                'URI: \'{}\''.format(uri))

		if script_path == None:
			raise Exception('Error: Invalid branch folder script path: ' \
			                '\'{}\''.format(scrip_path))

		if template_path == None or not os.path.isfile(template_path):
			raise IOError(errno.ENOENT, 'No such XML template path',
			              template_path)

		context = {
			'displayName': display,
			'numToKeep':   keepnr,
			'remote':      uri,
			'scriptPath':  script_path,
		}

		fdir, fname = os.path.split(template_path)
		load =jinja2.FileSystemLoader(fdir or './')
		env = jinja2.Environment(loader=load)
		conf = env.get_template(fname).render(context)

		# Create jobs folder
		self._server.create_job(name, conf)

		# Force scanning of created folder
		self._server.build_job(name)


	def sync_branch_folders(self, name_prefix, display_prefix, keepnr, uri,
	                        config_dirpath, script_path, template_path):
		if config_dirpath == None or not os.path.isdir(config_dirpath):
			raise IOError(errno.ENOENT, 'No such directory', config_dirpath)
		
		for f in glob.glob(os.path.join(config_dirpath, '*.config')):
			conf, _ = os.path.splitext(os.path.basename(f))

			name = '{}{}'.format(name_prefix, conf)
			if self._server.job_exists(name):
				continue

			print('creating \'{}\' multibranch folder'.format(name))
			self.create_branch_folder(name,
			                          '{} {}'.format(display_prefix, conf),
			                          keepnr, uri, script_path, template_path)


#print ci._server.get_job_config('greg-karn-slist_all')

if __name__ == '__main__':
	mainparse = argp.ArgumentParser(description = 'Manage CI jobs')
	mainparse.add_argument('-s', '--server', metavar = 'HOST_URL',
	                       type = str, nargs = 1,
	                       default = 'http://localhost:8080',
	                       help = 'server host URL')
	mainparse.add_argument('-u', '--user', metavar = 'USER_NAME',
	                       type = str, nargs = 1,
	                       default = os.environ['USER'],
	                       help = 'user used to authenticate against server ' \
	                              'host URL')
	mainparse.add_argument('-f', '--passwd_path', metavar = 'PASSWD_PATH',
	                       default = os.path.join(os.environ['HOME'], '.circ'),
	                       type = str, nargs = 1,
	                       help = 'plain password file path')
	subparse = mainparse.add_subparsers(dest = 'operation',
	                                    description = 'sub-commands')
	parse0 = subparse.add_parser('list_folders',
	                            help = 'list multibranch folders')
	parse0.add_argument('confdir', metavar = 'CONF_DIR',
	                    type = str, nargs = 1,
	                    help = 'jobs configuration directory')
	parse0.add_argument('prefix', metavar = 'PREFIX',
	                   type = str, nargs = 1,
	                   help = 'job names prefix')

	parse1 = subparse.add_parser('list_jobs',
	                            help = 'list multibranch jobs')
	parse1.add_argument('confdir', metavar = 'CONF_DIR',
	                   type = str, nargs = 1,
	                   help = 'jobs configuration directory')
	parse1.add_argument('prefix', metavar = 'PREFIX',
	                   type = str, nargs = 1,
	                   help = 'job names prefix')

	parse2 = subparse.add_parser('run_jobs',
	                            help = 'run multibranch jobs')
	parse2.add_argument('confdir', metavar = 'CONF_DIR',
	                   type = str, nargs = 1,
	                   help = 'jobs configuration directory')
	parse2.add_argument('prefix', metavar = 'PREFIX',
	                   type = str, nargs = 1,
	                   help = 'job names prefix')

	parse3 = subparse.add_parser('create_folder',
	                            help = 'create multibranch folder')
	parse3.add_argument('name', metavar = 'NAME',
	                   type = str, nargs = 1,
	                   help = 'multibranch folder name')
	parse3.add_argument('display', metavar = 'DISPLAY',
	                   type = str, nargs = 1,
	                   help = 'multibranch folder display name')
	parse3.add_argument('keepnr', metavar = 'KEEP_BUILD_NR',
	                   type = int, nargs = 1,
	                   help = 'number of multibranch job builds to keep')
	parse3.add_argument('uri', metavar = 'URI',
	                   type = str, nargs = 1,
	                   help = 'git repository URI')
	parse3.add_argument('script', metavar = 'SCRIPT_RELPATH',
	                   type = str, nargs = 1,
	                   help = 'script path relative to git repository URI')
	parse3.add_argument('template', metavar = 'TEMPLATE_PATH',
	                   type = str, nargs = 1,
	                   help = 'path to multibranch folder XML template')

	parse4 = subparse.add_parser('sync_folders',
	                            help = 'synchonize multibranch folders ' \
	                                   'against configurations')
	parse4.add_argument('name_prefix', metavar = 'NAME_PREFIX',
	                   type = str, nargs = 1,
	                   help = 'multibranch folders name prefix')
	parse4.add_argument('display_prefix', metavar = 'DISPLAY_PREFIX',
	                   type = str, nargs = 1,
	                   help = 'multibranch folders display name prefix')
	parse4.add_argument('keepnr', metavar = 'KEEP_BUILD_NR',
	                   type = int, nargs = 1,
	                   help = 'number of multibranch job builds to keep')
	parse4.add_argument('uri', metavar = 'URI',
	                   type = str, nargs = 1,
	                   help = 'git repository URI')
	parse4.add_argument('confdir', metavar = 'CONF_DIR',
	                    type = str, nargs = 1,
	                    help = 'jobs configuration directory')
	parse4.add_argument('script', metavar = 'SCRIPT_RELPATH',
	                   type = str, nargs = 1,
	                   help = 'script path relative to git repository URI')
	parse4.add_argument('template', metavar = 'TEMPLATE_PATH',
	                   type = str, nargs = 1,
	                   help = 'path to multibranch folder XML template')

	args = mainparse.parse_args()
	operation = args.operation

	try:
		secret = CiSecret()
		ci = Ci(args.server, args.user,
		        secret.get_from_plain_file(args.passwd_path))

		if operation == 'list_folders':
			for f in ci.list_branch_folders(args.confdir[0], args.prefix[0]):
				print(f)
		elif operation == 'list_jobs':
			for f in ci.list_branch_jobs(args.confdir[0], args.prefix[0]):
				print(f)
		elif operation == 'run_jobs':
			ci.run_branch_jobs(args.confdir[0], args.prefix[0])
		elif operation == 'create_folder':
			ci.create_branch_folder(args.name[0], args.display[0], args.keepnr[0],
			                        args.uri[0], args.script[0], args.template[0])
		elif operation == 'sync_folders':
			ci.sync_branch_folders(args.name_prefix[0], args.display_prefix[0],
			                       args.keepnr[0], args.uri[0],
		                           args.confdir[0], args.script[0],
		                           args.template[0])
	except Exception, e:
		print(e)
		sys.exit(1)
