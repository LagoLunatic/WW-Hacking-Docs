
# This script prints out the RAM location that each REL currently loaded is placed at.

# DMC = DynamicModuleControl. Information about each REL file. The list starts at 803B9218 in vanilla US Wind Waker.

import os

from mram_fs_helpers import *

DOLPHIN_MRAM_DUMP_PATH = os.path.expanduser("~/Documents/Dolphin Emulator/Dump/mem1.raw")

with open(DOLPHIN_MRAM_DUMP_PATH, "rb") as f:
  # Read a hardcoded reference to where the DMC list starts.
  # We do this instead of hardcoding the start of the DMC list directly because the randomizer changes this compared to vanilla.
  upper_halfword = read_u16(f, 0x80022818+2)
  lower_halfword = read_s16(f, 0x8002281C+2)
  dmc_list = (upper_halfword << 16) + lower_halfword
  
  # Read a hardcoded reference to the total number of actors.
  # We do this instead of hardcoding the number directly because the randomizer changes this compared to vanilla.
  num_actors = read_u16(f, 0x80022850+2)
  
  dynamic_name_table = 0x803398D8
  actor_id_to_rel_name = {}
  i = 0
  while True:
    actor_id = read_s16(f, dynamic_name_table + i*8 + 0)
    if actor_id == -1:
      break
    rel_filename_ptr = read_u32(f, dynamic_name_table + i*8 + 4)
    rel_filename = read_str_until_null_character(f, rel_filename_ptr)
    actor_id_to_rel_name[actor_id] = rel_filename
    i += 1
  
  print("%08X %04X" % (dmc_list, num_actors))
  for actor_id in range(num_actors):
    dmc_pointer = read_u32(f, dmc_list + actor_id*4)
    if dmc_pointer == 0:
      # Not an actor with a REL file.
      continue
    rel_pointer = read_u32(f, dmc_pointer+0x10)
    if rel_pointer == 0:
      # REL is not currently loaded.
      continue
    
    rel_filename = actor_id_to_rel_name[actor_id]
    print("%04X %08X %s" % (actor_id, rel_pointer, rel_filename))
