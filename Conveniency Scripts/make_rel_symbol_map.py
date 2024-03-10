
# This script outputs a custom framework.map that includes not only the main.dol symbols, but also
# the REL symbols for all currently loaded RELs, adjusted to the appropriate addresses.
# It also automatically detects the version of the game (USA, JPN, PAL) and supports all three.

import os
import re

from mram_fs_helpers import *

DOLPHIN_MRAM_DUMP_PATH = os.path.expanduser("~/Documents/Dolphin Emulator/Dump/mem1.raw")
DOLPHIN_MAPS_FOLDER = os.path.expanduser("~/Documents/Dolphin Emulator/Maps")
DOLPHIN_AUTO_MAP_PATH = os.path.join(DOLPHIN_MAPS_FOLDER, "TWW_Framework_With_REL_Symbols.map")
VERSION_TO_MAPS_FOLDER = {
  "GZLJ": "D:/WW/WW JPN Files Extracted/files/maps",
  "GZLE": "D:/WW/Wind Waker Files Extracted/files/maps",
  "GZLP": None,
}

def get_main_symbols(framework_map_contents):
  main_symbols = {}
  
  sections = re.split(r"(\S+ section layout)", framework_map_contents)
  if sections[0] == "":
    sections.pop(0)
  for section_header, section_contents in zip(sections[::2], sections[1::2]):
    section_name, section_layout_str = section_header.split(" ", 1)
    assert section_layout_str == "section layout"
    
    matches = re.findall(r"^  [0-9a-f]{8} ([0-9a-f]{6}) ([0-9a-f]{8})(?: +\d+)? (.+?)(?: \(entry of [^)]+\))? \t", section_contents, re.IGNORECASE | re.MULTILINE)
    for match in matches:
      size, address, name = match
      size = int(size, 16)
      address = int(address, 16)
      main_symbols[name] = (address, size, section_name)
  
  return main_symbols

def get_rel_symbols(mram, rel_address, rel_map_data):
  rel_map_lines = rel_map_data.splitlines()
  found_memory_map = False
  next_section_index = 0
  section_name_to_section_index = {}
  for line in rel_map_lines:
    if line.strip() == "Memory map:":
      found_memory_map = True
    if found_memory_map:
      section_match = re.search(r"^ +\.(text|ctors|dtors|rodata|data|bss)  [0-9a-f]{8} ([0-9a-f]{8}) [0-9a-f]{8}$", line)
      if section_match:
        section_name = section_match.group(1)
        section_size = int(section_match.group(2), 16)
        if section_size > 0:
          section_name_to_section_index[section_name] = next_section_index
          next_section_index += 1
  if not found_memory_map:
    raise Exception("Failed to find memory map")
  
  rel_symbols = {}
  
  section_index_to_address = {}
  num_sections = read_u32(mram, rel_address+0x0C)
  section_info_table_address = read_u32(mram, rel_address+0x10)
  section_index = 0
  for i in range(0, num_sections):
    section_info_address = section_info_table_address + i*8
    section_address = read_u32(mram, section_info_address+0x00) & ~1
    section_size = read_u32(mram, section_info_address+0x04)
    if section_size != 0:
      section_index_to_address[section_index] = section_address
      section_index += 1
  
  current_section_name = None
  current_section_index = None
  current_section_address = None
  for line in rel_map_lines:
    section_header_match = re.search(r"^\.(text|ctors|dtors|rodata|data|bss) section layout$", line)
    if section_header_match:
      current_section_name = section_header_match.group(1)
      if current_section_name in section_name_to_section_index:
        current_section_index = section_name_to_section_index[current_section_name]
        current_section_address = section_index_to_address[current_section_index]
      else:
        current_section_index = None
        current_section_address = None
    
    symbol_entry_match = re.search(r"^  ([0-9a-f]{8}) ([0-9a-f]{6}) ([0-9a-f]{8})(?: +(\d+))? (.+?)(?: \(entry of [^)]+\))? \t(\S+)", line, re.IGNORECASE)
    if current_section_address is not None and symbol_entry_match:
      if current_section_address == 0:
        raise Exception("Found symbol in section with address 0")
      starting_address = int(symbol_entry_match.group(1), 16)
      symbol_size = int(symbol_entry_match.group(2), 16)
      virtual_offset = int(symbol_entry_match.group(3), 16)
      virtual_address = virtual_offset + current_section_address
      symbol_alignment = symbol_entry_match.group(4)
      if symbol_alignment:
        symbol_alignment = int(symbol_alignment, 10)
      symbol_name = symbol_entry_match.group(5)
      translation_unit = symbol_entry_match.group(6)
      rel_symbols[symbol_name] = (starting_address, symbol_size, virtual_address, symbol_alignment, symbol_name, translation_unit, current_section_name)
      #print("%08X  %s" % (symbol_offset, symbol_name))
  
  #print(rel_symbols)
  
  return rel_symbols

def get_all_loaded_rel_symbols(version_maps_folder, main_symbols):
  rel_name_to_rel_symbols = {}
  
  with open(DOLPHIN_MRAM_DUMP_PATH, "rb") as mram:
    # Read a hardcoded reference to where the DMC list starts.
    # We do this instead of hardcoding the start of the DMC list directly because the randomizer changes this compared to vanilla.
    cCc_Init_addr = main_symbols["cCc_Init__Fv"][0]
    upper_halfword = read_u16(mram, cCc_Init_addr+0x78+2)
    lower_halfword = read_s16(mram, cCc_Init_addr+0x7C+2)
    dmc_list = (upper_halfword << 16) + lower_halfword
    
    # Read a hardcoded reference to the total number of actors.
    # We do this instead of hardcoding the number directly because the randomizer changes this compared to vanilla.
    num_actors = read_u16(mram, cCc_Init_addr+0xB0+2)
    
    DynamicNameTable_addr = main_symbols["DynamicNameTable"][0]
    actor_id_to_rel_name = {}
    i = 0
    while True:
      actor_id = read_s16(mram, DynamicNameTable_addr + i*8 + 0)
      if actor_id == -1:
        break
      rel_filename_ptr = read_u32(mram, DynamicNameTable_addr + i*8 + 4)
      rel_filename = read_str_until_null_character(mram, rel_filename_ptr)
      actor_id_to_rel_name[actor_id] = rel_filename
      i += 1
    
    print(f"{dmc_list=:08X} {num_actors=:04X}")
    print("actor_id rel_pointer rel_filename")
    for actor_id in range(num_actors):
      dmc_pointer = read_u32(mram, dmc_list + actor_id*4)
      if dmc_pointer == 0:
        # Not an actor with a REL file.
        continue
      rel_pointer = read_u32(mram, dmc_pointer+0x10)
      if rel_pointer == 0:
        # REL is not currently loaded.
        continue
      
      rel_filename = actor_id_to_rel_name.get(actor_id, "[unknown - custom]")
      print("%04X %08X %s" % (actor_id, rel_pointer, rel_filename))
      #rel_filename_to_rel_address[rel_filename] = rel_pointer
      
      orig_rel_map_path = os.path.join(version_maps_folder, rel_filename + ".map")
      with open(orig_rel_map_path) as f:
        rel_map_data = f.read()
      rel_symbols = get_rel_symbols(mram, rel_pointer, rel_map_data)
      #print(rel_symbols)
      rel_name_to_rel_symbols[rel_filename] = rel_symbols
  
  return rel_name_to_rel_symbols

if __name__ == "__main__":
  with open(DOLPHIN_MRAM_DUMP_PATH, "rb") as mram:
    game_id = read_str(mram, 0x80000000, 4)
  print(game_id)
  version_maps_folder = VERSION_TO_MAPS_FOLDER[game_id]
  if version_maps_folder is None:
    raise Exception(f"No extracted maps folder specified for version {game_id}")
  with open(os.path.join(version_maps_folder, "framework.map")) as f:
    framework_map_contents = f.read()
  main_symbols = get_main_symbols(framework_map_contents)
  loaded_rel_symbols = get_all_loaded_rel_symbols(version_maps_folder, main_symbols)
  
  with open(DOLPHIN_AUTO_MAP_PATH, "w") as f:
    f.write(framework_map_contents + "\n")
    #f.write(".text section layout\n")
    for rel_filename, rel_symbols in loaded_rel_symbols.items():
      for symbol_name, (starting_address, symbol_size, virtual_address, symbol_alignment, symbol_name, translation_unit, current_section_name) in rel_symbols.items():
        if symbol_alignment is None:
          symbol_alignment = ""
        else:
          symbol_alignment = f" {symbol_alignment:d} "
        
        f.write(f"  {starting_address:08x} {symbol_size:06x} {virtual_address:08x} {symbol_alignment}{symbol_name} \t{translation_unit} \n")
