#!/usr/bin/env python
"""
BIONICLE: The Legend of Mata Nui Executable Patcher for build Alpha 0.006
Version: 1.1.0

Copyright (c) 2018 JrMasterModelBuilder
Licensed under the Mozilla Public License, v. 2.0
"""

import os
import sys
import inspect
import argparse

def nops(length):
	return [0x90] * length

def nop_pad(data, length):
	l = len(data)
	pad = length - l
	if pad < 0:
		raise Exception('Longer than padded length: %s > %s' % (l, length))
	return data + nops(pad)

class Patch():
	def __init__(self, fp):
		self.fp = fp

class PatchWin10(Patch):
	name = 'win10'
	description = 'Windows 10'
	def patch(self):
		# Check if pointer is -1, and if so always throw an exception.
		# In Windows 10 CloseHandle(-1) no longer returns -1 (undefined behavior).
		self.fp.seek(0x9AE93) # 0x49BA93
		self.fp.write(bytearray([
			# Inserted before existing code.
			0x83, 0xBB, 0x24, 0x01, 0x00, 0x00, 0xFF, # cmp    DWORD PTR [ebx+0x124], 0xffffffff
			0x74, 0x04,                               # je     0xd
			# Existing code, shifted down, addresses corrected.
			0x85, 0xC0,                               # test   eax, eax
			0x75, 0x11,                               # jne    0x1e
			0x68, 0x8C, 0xBA, 0x69, 0x00,             # push   0x69ba8c
			0x68, 0xB0, 0xBA, 0x69, 0x00,             # push   0x69bab0
			0xE8, 0xA1, 0xEF, 0xFF, 0xFF,             # call   0xffffefb0
			0x59,                                     # pop    ecx
			0x59,                                     # pop    ecx
			0xC6, 0x83, 0x20, 0x01, 0x00, 0x00, 0x00, # mov    BYTE PTR [ebx+0x120], 0x0
			0x8D, 0x65, 0xFC,                         # lea    esp, [ebp-0x4]
			0x5B,                                     # pop    ebx
			0x5D,                                     # pop    ebp
			0xC3                                      # ret
		]))

class PatchSoundTableAmount(Patch):
	name = 'soundtableamount'
	description = 'Avoid SoundTable error message'
	def patch(self):
		# Change expected amount of SoundTable entries to avoid error message.
		self.fp.seek(0x14E374) # 0x54EF74
		self.fp.write(bytearray([
			0x81, 0xBD, 0xD4, 0xFE, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF
		]))

class PatchScreenRes4(Patch):
	name = 'screenres4'
	description = 'Set default screen resolution to 4'
	def patch(self):
		# Replace the default resolution int of 2 with the max of 4.
		self.fp.seek(0x22CAE4) # 0x62F0E4
		self.fp.write(bytearray([
			0x04
		]))

class PatchScreenResINI(Patch):
	name = 'screenresini'
	description = 'Allow ini to control screen resolution'
	def patch(self):
		# Replace GcGraphicsOptions::GetScreenResolution call in AppMain with constant 0.
		# This will force switch default case and prevent overwriting values from INI.
		self.fp.seek(0xCFFD5) # 0x4D0BD5
		self.fp.write(bytearray([
			0xB8, 0x00, 0x00, 0x00, 0x00 # mov    eax, 0x0
		]))

		# Replace GcGraphicsOptions::GetScreenResolution switch statement in ScDrawableContext::Reset.
		# Instead call GcSaver::GetScreenData with the 7 required pointer arguments.
		# For the last 5 arguments, use a stack address that will be overwritten after this call.
		# For the first 2 arguments, pass the address of the height and width.
		# This code is somewhat unconventional and may look odd when run through a pseudocode generator.
		self.fp.seek(0xEB253) # 0x4EBE53
		self.fp.write(bytearray(nop_pad([
			0x8D, 0x85, 0x34, 0xFF, 0xFF, 0xFF, # lea     eax, [ebp-0xCC]
			0x50,                               # push    eax
			0x50,                               # push    eax
			0x50,                               # push    eax
			0x50,                               # push    eax
			0x50,                               # push    eax
			0x8D, 0x85, 0x30, 0xFF, 0xFF, 0xFF, # lea     eax, [ebp-0xD0]
			0x50,                               # push    eax
			0x8D, 0x85, 0x2C, 0xFF, 0xFF, 0xFF, # lea     eax, [ebp-0xD4]
			0x50,                               # push    eax
			0xE8, 0xCF, 0xAE, 0x06, 0x00,       # call    ?GetScreenData@GcSaver@@SAXAAG0AAE1111@Z
			0x83, 0xC4, 0x1C                    # add     esp, 0x1C
		], 0x71)))

		# Replace GcGraphicsOptions::GetScreenResolution switch statement in ScPlatformScreen::BuildDeviceList.
		# Instead of reading config values do what build 2001-10-23 does and use the existing struct.
		# ScPlatformScreen -> ScScreen -> ScScreenData -> <float pair 2>.
		# In build 2001-10-23 the following code compares these floats against ints, but this version expects ints.
		# Cast the floats to integers, since the floats will never have point values, no need to handle them.
		self.fp.seek(0xCA978) # 0x4CB578
		self.fp.write(bytearray(nop_pad([
			0x8B, 0x85, 0x20, 0xF8, 0xFF, 0xFF, # mov     eax, DWORD PTR [ebp-0x7E0]
			0x8B, 0x40, 0x04,                   # mov     eax, DWORD PTR [eax+0x4]
			0xD9, 0x40, 0x10,                   # fld     DWORD PTR [eax+0x10]
			0xDB, 0x9D, 0x24, 0xF8, 0xFF, 0xFF, # fistp   DWORD PTR [ebp-0x7DC]
			0x8B, 0x85, 0x20, 0xF8, 0xFF, 0xFF, # mov     eax, DWORD PTR [ebp-0x7E0]
			0x8B, 0x40, 0x04,                   # mov     eax, DWORD PTR [eax+0x4]
			0xD9, 0x40, 0x14,                   # fld     DWORD PTR [eax+0x14]
			0xDB, 0x9D, 0x28, 0xF8, 0xFF, 0xFF  # fistp   DWORD PTR [ebp-0x7D8]
		], 0x72)))

class PatchHVP(Patch):
	name = 'hvp'
	description = 'Hardward vertex processing'
	def patch(self):
		# By default the game attempts to draw with a negative near and far clip.
		# This does not work on any known graphics cards and is apparently very wrong.
		# This patch disables all the world inverting things that relate to this.
		# Most of these changes are side effects to enabling SVP.
		# Essentially this patch corrects hardware vertex processing mode.

		# Disable negative near and far clip on the camera in GcViewPort::GcViewPort.
		# Nop over the comparison and jump code to force the first branch.
		self.fp.seek(0x3B924) # 0x43C524
		self.fp.write(bytearray(nops(13)))

		# Disable inverted view matrix in GcLegoCamera::BuildViewMatrix.
		# Nop over the comparison and jump code to force the first branch.
		self.fp.seek(0x4BC80) # 0x44C880
		self.fp.write(bytearray(nops(13)))

		# Disable inverted fog values in GcAreaDirector::SetFog.
		# Nop over the comparison and jump code to force the first branch.
		self.fp.seek(0x71D93) # 0x472993
		self.fp.write(bytearray(nops(9)))

		# Disable inverted projection matrix in ScPerspectiveCamera::BuildProjectionMatrix.
		# Nop over the comparison and jump code to force the first branch.
		self.fp.seek(0x79526) # 0x47A126
		self.fp.write(bytearray(nops(9)))

		# Replace float sign inversion in GcGraphicsOptions::SetDrawDistance.
		# Nop over the comparison and jump code to force the first branch.
		self.fp.seek(0x15FBB0) # 0x5607B0
		self.fp.write(bytearray(nops(9)))

		# Replace float sign inversion in GcGraphicsOptions::GetDrawDistance.
		# Nop over the comparison and jump code to force the first branch.
		self.fp.seek(0x15FBE0) # 0x5607E0
		self.fp.write(bytearray(nops(9)))

		# Replace PI float with 0.0 in ScMatrix::RotateZ(PI) of GcSprite:Render.
		# Stop 2D sprites from being being flipped upside down.
		self.fp.seek(0x21B88C) # 0x61DE8C
		self.fp.write(bytearray([
			0x00, 0x00, 0x00, 0x00 # float 0.0
		]))

class PatchBitDepth24(Patch):
	name = 'bitdepth24'
	description = 'Set the bit depth to 24'
	def patch(self):
		# Windowed mode.
		# Set AutoDepthStencilFormat to D3DFMT_D24X8 (0x4D), not D3DFMT_D16 (0x50).
		self.fp.seek(0xCB4F8) # 0x4CC0F8
		self.fp.write(bytearray([
			0x4D
		]))

		# Fullscreen mode.
		# Set m_dwMinDepthBits to 24 (0x18), not 16 (0x10).
		self.fp.seek(0xCB5BD) # 0x4CC1BD
		self.fp.write(bytearray([
			0x18
		]))

def patches_list():
	prefix = 'Patch'
	root = globals().copy()
	r = []
	for k, v in root.items():
		if not inspect.isclass(v):
			continue
		if not k.startswith(prefix):
			continue
		if k == prefix:
			continue
		if not hasattr(v, 'name'):
			continue
		if not hasattr(v, 'description'):
			continue
		r.append(v)
	return r

def patches_filtered(enabled, disabled):
	all_patches = patches_list()
	r = []

	if enabled:
		set_e = set(enabled)
		for patch in all_patches:
			if patch.name in set_e:
				r.append(patch)
	elif disabled:
		set_d = set(disabled)
		for patch in all_patches:
			if not patch.name in set_d:
				r.append(patch)
	else:
		r = all_patches

	return r

def process(args):
	patches = patches_filtered(args.enabled, args.disabled)
	with open(args.file[0], 'rb+') as fp:
		for Patch in patches:
			fp.seek(0)
			print('Patching: %s: %s' % (Patch.name, Patch.description))
			Patch(fp).patch()
		fp.close()
	print('Done')

def main():
	# List all the patches for the help info.
	patches = patches_list()
	patches_help = []
	for patch in patches:
		patches_help.append('  %s %s' % (patch.name.ljust(21), patch.description))

	parser = argparse.ArgumentParser(
		description=os.linesep.join([
			'TLOMN Build Alpha 0.006 Patcher',
			'Version: 1.1.0'
		]),
		epilog=os.linesep.join([
			'patches:',
			os.linesep.join(patches_help),
			'',
			'Copyright (c) 2018 JrMasterModelBuilder',
			'Licensed under the Mozilla Public License, v. 2.0'
		]),
		formatter_class=argparse.RawTextHelpFormatter
	)

	group_enable_disable = parser.add_mutually_exclusive_group()
	group_enable_disable.add_argument(
		'-e',
		'--enabled',
		action='append',
		help='Only apply listed patches'
	)
	group_enable_disable.add_argument(
		'-d',
		'--disabled',
		action='append',
		help='No not apply listed patches'
	)

	parser.add_argument(
		'file',
		nargs=1,
		help='File to be patched'
	)

	return process(parser.parse_args())

if __name__ == '__main__':
	sys.exit(main())
