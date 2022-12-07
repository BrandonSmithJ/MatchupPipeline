from . import run_tests, OUTPUT_FOLDER

from ..API.sources.__test__ import get_tests as API_tests
from ..AC.L2_processing.__test__ import get_tests as AC_tests

if __name__ == '__main__':
	class Args:
		show_traceback = True
		show_warnings  = True
		show_debugs    = True
		halt_on_fail   = True
		output_folder  = OUTPUT_FOLDER

	run_tests(Args, AC_tests())
