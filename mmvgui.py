import subprocess
import os
import sys

import numpy as np
import PySimpleGUIQt as sg
import json


#

def help_window(filepath):
	with open(filepath, 'r') as f:
		data = json.load(f)
	help_layout = [[sg.Text(text=data['explanation'])],[sg.Text(text=data['examples'])]]

	return sg.Window("mmvgui Help", layout=help_layout) 

#end def

def preview(window, values):
	#get text
	fromText = values['from_string']
	toText = values['to_string']
	
	if not fromText or not toText or not fromText.strip() or not toText.strip():
		return
	#end if

	#pass to mmv with --no-execute
	command = [x.encode('UTF-8') for x in ['mmv', '-n', '--', fromText, toText]]
	try:	
		result = subprocess.run(command, capture_output=True, timeout=1, cwd=values['folder_input'].strip()).stdout.decode('UTF-8')
	except Exception:
		result = 'Error'
	#end except
	if not result:
		return
	#endif

	# get from and to files (separated by '->')

	result =  np.array(result.split('\n'), dtype=object)
	fromFiles = np.full(result.shape, "", dtype=object)
	toFiles = np.full(result.shape, "", dtype=object)

	for i, x in enumerate(result):
		if '->' in result[i]:
			fromFiles[i], toFiles[i] = x.split('->')
		elif '=^' in result[i]:
			fromFiles[i], toFiles[i] = x.split('=^')
		else:
			fromFiles[i] = x
		#end else
	#end for

	fromFiles = np.array2string(fromFiles,separator='\n')
	toFiles = np.array2string(toFiles,separator='\n')

	#set text
	window['from_files'](fromFiles)
	window['to_files'](toFiles)

#end def

def execute(window, values):
	modal_layout = [[sg.Text('Are you sure?')],
					[sg.No(focus=True),sg.Yes()]]	
	# create modal window
	modal_window = sg.Window("Confirm mmv", layout=modal_layout)
	# confirm
	event, _ = modal_window.read(timeout=60000)

	if event != 'Yes':
		modal_window.close()		
		return False
	#end if
	#get text
	fromText = values['from_string']
	toText = values['to_string']
	
	#pass to mmv
	command = command = [x.encode('UTF-8') for x in ['mmv', '--', fromText, toText]]
	try:
		results = subprocess.run(command, capture_output=True, timeout=1, cwd=values['folder_input'].strip())
	except Exception:
		error_window('error')
	#end except

	modal_window.close()

	if results.returncode!=0:
		#error
		error_window(results.stderr.decode('UTF-8'))
	#end if
	return True
#end def

def error_window(msg):

	error_layout = [[sg.Multiline(key='msg')],[sg.Ok(focus=True)]]
	modal_window = sg.Window("Error", layout=error_layout)
	modal_window['msg'](msg)
	modal_window.ding()
	modal_window.read(timeout=60000)
	modal_window.close()
#end def

if __name__=="__main__":
	config_name = 'mmvgui.cfg'
	help_name = 'mmvgui_help.json'
	# determine if application is a script file or frozen exe
	if getattr(sys, 'frozen', False):
	    application_path = os.path.dirname(sys.executable)
	elif __file__:
	    application_path = os.path.dirname(__file__)
	
	config_path = os.path.join(application_path, config_name)
	help_path = os.path.join(application_path, help_name)	

	helpWindow = None
	
	#
	if not os.path.isfile(config_path):
		defaultFolder = subprocess.run(['pwd'], capture_output=True).stdout.decode('UTF-8')
		defaultFrom = ''
		defaultTo = ''
	else:
		with open(config_path, 'r') as f:
			config = json.load(f)			
			defaultFolder = config['defaultFolder']
			defaultFrom = config['defaultFrom']
			defaultTo = config['defaultTo']
		#end with
	#end else
	layout = [[sg.Text('Folder:',), sg.InputText(defaultFolder,key='folder_input', enable_events=True), sg.FolderBrowse(key='folder_choose',enable_events=True), sg.Help()], 
			[sg.Text('Source string'), sg.Text('Target string')],
			[sg.Input(defaultFrom, key='from_string', enable_events=True), sg.Input(defaultTo, key='to_string', enable_events=True)],
			[sg.Multiline(key='from_files'), sg.Multiline(key='to_files')],
			[sg.Button(button_text='Go')]]
	#end layout

	window = sg.Window("mmvgui", layout=layout)
	changed = True
	while True:
		event, values = window.read(timeout=500)
		if (event=='__TIMEOUT__'):
			if changed:
				preview(window, values)
				changed = False
			#end if
		elif event=='Go':
			changed = execute(window, values)
		elif event=='folder_choose':
			changed = True
			folder = values['folder_choose']
			if not os.path.isdir(folder):
				folder = os.path.dirname(folder)
			#endif
			window['folder_input'](folder)
		elif event=='Help':
			helpWindow = help_window(help_path)
			helpWindow.read()
		elif event==sg.WIN_CLOSED:
			with open(config_path, 'w') as f:
				json.dump(config, f)
			break
		else:
			changed = True			
		#end else
		config = {'defaultFolder':values['folder_input'],'defaultFrom':values['from_string'],'defaultTo':values['to_string']}
	
	if helpWindow:
		helpWindow.close()
	window.close()
#end if


#eof
