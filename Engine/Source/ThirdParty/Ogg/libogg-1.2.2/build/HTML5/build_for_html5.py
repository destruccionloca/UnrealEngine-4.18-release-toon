import subprocess, os, shutil, sys

# This script builds Ogg for HTML5 using Esmcripten.
# Usage:
#  1. Activate emsdk in the current command prompt
#  2. Run "python path/to/build_for_html5.py"

if not os.getenv('EMSCRIPTEN'):
	print >> sys.stderr, 'Environment variable EMSCRIPTEN not set! Please first install and activate emsdk in current cmd prompt.'
	sys.exit(1)

def bat_file(cmd):
	return (cmd + '.bat') if os.name == 'nt' else cmd

def run(cmd):
	print str(cmd)
	subprocess.check_call(cmd)

build_modes = [('', 'Debug'),
               ('-O2', 'Release'),
               ('-O3', 'Release'),
               ('-Oz', 'MinSizeRel')]

src_directory = os.path.normpath(os.path.join(os.path.realpath(os.path.dirname(__file__)), '..', '..'))
print 'Build source directory: ' + src_directory

output_lib_directory = os.path.normpath(os.path.join(src_directory, 'lib', 'HTML5'))
if 'rebuild' in sys.argv:
	try:
		for f in [os.path.join(output_lib_directory, f) for f in os.listdir(output_lib_directory) if f.endswith(".bc")]:
			print 'Clearing ' + f
			os.remove(f)
	except Exception, e:
		pass

print 'Output libraries to directory: ' + output_lib_directory

for (mode, cmake_build_type) in build_modes:
	print 'Building ' + mode + ', ' + cmake_build_type + ':'

	# Create and move to the build directory for this configuration.
	build_dir = os.path.join(src_directory, 'html5_build' + mode.replace('-', '_'))
	print 'Artifacts directory for build: ' + build_dir
	if os.path.exists(build_dir) and 'rebuild' in sys.argv: shutil.rmtree(build_dir)
	if not os.path.exists(build_dir): os.mkdir(build_dir)
	os.chdir(build_dir)

	# C & C++ compiler flags to use for the build.
	compile_flags = mode
	compile_flags += ' -D_DEBUG ' if cmake_build_type == 'Debug' else ' -DNDEBUG '
	compile_flags = ['-DCMAKE_C_FLAGS_' + cmake_build_type.upper() + '=' + compile_flags,
		'-DCMAKE_CXX_FLAGS_' + cmake_build_type.upper() + '=' + compile_flags,
		'-DCMAKE_STATIC_LINKER_FLAGS_' + cmake_build_type.upper() + '=' + mode,
		'-DCMAKE_SHARED_LINKER_FLAGS_' + cmake_build_type.upper() + '=' + mode,
		'-DCMAKE_MODULE_LINKER_FLAGS_' + cmake_build_type.upper() + '=' + mode,
		'-DCMAKE_EXE_LINKER_FLAGS_' + cmake_build_type.upper() + '=' + mode]

	# Configure the build via CMake
	run([os.path.join(os.getenv('EMSCRIPTEN'), bat_file('emcmake')), 'cmake', '-DBUILD_SHARED_LIBS=OFF', '-DEMSCRIPTEN_GENERATE_BITCODE_STATIC_LIBRARIES=ON', '-DCMAKE_BUILD_TYPE=' + cmake_build_type] + compile_flags + ['..'])

	# Run the build
	cmd = ['cmake', '--build', '.', '--', '-j']
	if 'verbose' in sys.argv: cmd += ['VERBOSE=1']
	run(cmd)

	# Deploy the output to the libraries directory.
	output_file = os.path.join(output_lib_directory, 'libogg' + mode.replace('-', '_') + '.bc')
	print 'Deploying ' + output_file
	shutil.copyfile(os.path.join(build_dir, 'libogg.bc'), output_file)
