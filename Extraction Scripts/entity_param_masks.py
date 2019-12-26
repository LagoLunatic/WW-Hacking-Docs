
# This script reads through the ASM code of all REL files in the game and attempts to extract all of the masks for their parameters automatically.
# It's not 100% accurate, it does have a number of cases where the masks it detects either overlap with each other or are noncontiguous.
# But generally speaking, almost all of its masks are correct, and the ones that are incorrect are usually obvious.
# Note that it does not detect parameter masks for entities that have their code in the main executable such as items. Only entities that have their own REL file.

ACTOR_INFO_TEXT_FILE_PATH = "../Extracted Data/Actor Info.txt"
DISASSEMBLED_CODE_FILES_FOLDER = "../../disassemble"

import re
import os
import glob

with open(ACTOR_INFO_TEXT_FILE_PATH, "r") as f:
  actor_info_str = f.read()
actor_info_matches = re.findall(
  r" *(\S+):   ID ([0-9a-f]+),   Subtype ([0-9a-f]+),   Unknown ([0-9a-f]+),   REL (\S+)",
  actor_info_str, re.IGNORECASE
)
actor_names_by_rel_name = {}
for actor_name, rel_id, subtype, unknown, rel_name in actor_info_matches:
  if rel_name not in actor_names_by_rel_name:
    actor_names_by_rel_name[rel_name] = []
  actor_names_by_rel_name[rel_name].append(actor_name)

ALL_OVERWRITING_OPCODES = [
  "lbz",
  "lbzu",
  "lbzux",
  "lbzx",
  
  "lha",
  "lhau",
  "lhaux",
  "lhax",
  "lhbrx",
  "lhz",
  "lhzu",
  "lhzux",
  "lhzx",
  
  "lmw",
  "lswi",
  "lswx",
  "lwarx",
  "lwbrx",
  "lwz",
  "lwzu",
  "lwzux",
  "lwzx",
  
  "mr",
  
  "add",
  "addi",
  "addis",
  "sub",
  "subi",
  "subis",
  "subfic",
  
  "cntlzw",
  
  "lis",
  "li",
  
  "neg",
  
  "rlwinm",
  "clrlwi",
  "rotlwi",
  
  "slw",
  "sraw",
  "srawi",
  "srwx",
]

def add_mask_to_list(list, bit_mask, line, func_name):
  offset_match = re.search(r"^\s+([0-9a-f]+):", line, re.IGNORECASE)
  offset = int(offset_match.group(1), 16)
  
  code_line = "Read at %04X in func %s" % (offset, func_name)
  
  for other_bit_mask, other_code_lines in list:
    if other_bit_mask == bit_mask:
      other_code_lines.append(code_line)
      return
  
  list.append((bit_mask, [code_line]))

final_output_string = ""
final_output_string_with_code_lines = ""
all_asm_files = glob.glob(DISASSEMBLED_CODE_FILES_FOLDER + "/*.asm")
for asm_file in all_asm_files:
  rel_name = os.path.splitext(os.path.basename(asm_file))[0]
  if rel_name == "main":
    continue
  #if rel_name != "d_a_obj_swpush":
  #  continue
  
  print("%s:" % rel_name)
  final_output_string += "%s:\n" % rel_name
  final_output_string_with_code_lines += "%s:\n" % rel_name
  
  if rel_name in actor_names_by_rel_name:
    actor_names = actor_names_by_rel_name[rel_name]
  else:
    actor_names = []
  actor_names_str = "  Actor names: %s" % (", ".join(actor_names))
  print(actor_names_str)
  final_output_string += actor_names_str + "\n"
  final_output_string_with_code_lines += actor_names_str + "\n"
  
  with open(DISASSEMBLED_CODE_FILES_FOLDER + "/%s.asm" % rel_name) as f:
    lines = f.read().split("\n")

  all_bit_masks = {
    "params": [],
    "aux_params_1": [],
    "aux_params_2": [],
  }
  all_bit_masks_for_subclass = {
    "params": [],
    "aux_params_1": [],
    "aux_params_2": [],
  }
  all_registers = {}
  for i in range(0, 31+1):
    all_registers["r%d" % i] = None
  last_seen_symbol_name = ""
  for line_index, line in enumerate(lines):
    curr_bit_masks_list = all_bit_masks
    if "_sub(" in last_seen_symbol_name:
      # functions that have names ending in _sub might be for sub-objects, not the main object in question.
      # as in, the "this" passed to the function is not the entity we want.
      # for example, bokoblins have some functions for their sword, which read the sword parameters from "this" instead of bokoblin parameters.
      curr_bit_masks_list = all_bit_masks_for_subclass
    
    prmabstract_match = re.search(r" 	bl      0x[0-9a-f]+      ; PrmAbstract<", line, re.IGNORECASE)
    
    lwz_match = re.search(r" 	lwz     (r\d+),(\d+)\((r\d+)\)", line, re.IGNORECASE)
    lha_match = re.search(r" 	lha     (r\d+),(\d+)\((r\d+)\)", line, re.IGNORECASE)
    lwz_params_match = None
    lha_aux_params_1_match = None
    lha_aux_params_2_match = None
    had_any_successful_load_match = False
    
    if lwz_match:
      if all_registers[lwz_match.group(3)] == "entity":
        if lwz_match.group(2) == "176":
          lwz_params_match = lwz_match
          had_any_successful_load_match = True
      lwz_match = None
    if lha_match:
      if all_registers[lha_match.group(3)] == "entity":
        if lha_match.group(2) in ["476", "516", "524"]:
          lha_aux_params_1_match = lha_match
          had_any_successful_load_match = True
        elif lha_match.group(2) in ["480", "520", "528"]:
          lha_aux_params_2_match = lha_match
          had_any_successful_load_match = True
      lha_match = None
    
    
    should_invert_curr_mask = False
    
    rlwinm_match = re.search(r" 	rlwinm\.?\s+(r\d+),(r\d+),(\d+),(\d+),(\d+)", line, re.IGNORECASE)
    clrlwi_match = re.search(r" 	clrlwi\.?\s+(r\d+),(r\d+),(\d+)", line, re.IGNORECASE)
    stb_match = re.search(r" 	stb     (r\d+),\d+\(r\d+\)", line, re.IGNORECASE)
    #sth_match = re.search(r" 	sth     (r\d+),\d+\(r\d+\)", line, re.IGNORECASE)
    cmplwi_match = re.search(r" 	cmplwi  (r\d+),\d+", line, re.IGNORECASE)
    cmpw_match = re.search(r" 	cmpw    (r\d+),(r\d+)", line, re.IGNORECASE)
    
    curr_mask_attribute_name = None
    if rlwinm_match and all_registers[rlwinm_match.group(2)] in ["params", "aux_params_1", "aux_params_2"]:
      curr_mask_attribute_name = all_registers[rlwinm_match.group(2)]
    else:
      rlwinm_match = None
    if clrlwi_match and all_registers[clrlwi_match.group(2)] in ["params", "aux_params_1", "aux_params_2"]:
      curr_mask_attribute_name = all_registers[clrlwi_match.group(2)]
    else:
      clrlwi_match = None
    if stb_match and all_registers[stb_match.group(1)] in ["params", "aux_params_1", "aux_params_2"]:
      curr_mask_attribute_name = all_registers[stb_match.group(1)]
    else:
      stb_match = None
    #if sth_match and all_registers[sth_match.group(1)] in ["params", "aux_params_1", "aux_params_2"]:
    #  curr_mask_attribute_name = all_registers[sth_match.group(1)]
    #else:
    #  sth_match = None
    if cmplwi_match and all_registers[cmplwi_match.group(1)] in ["params", "aux_params_1", "aux_params_2"]:
      curr_mask_attribute_name = all_registers[cmplwi_match.group(1)]
    else:
      cmplwi_match = None
    if cmpw_match and all_registers[cmpw_match.group(1)] in ["params", "aux_params_1", "aux_params_2"]:
      curr_mask_attribute_name = all_registers[cmpw_match.group(1)]
    elif cmpw_match and all_registers[cmpw_match.group(2)] in ["params", "aux_params_1", "aux_params_2"]:
      curr_mask_attribute_name = all_registers[cmpw_match.group(2)]
    else:
      cmpw_match = None
    
    
    if rlwinm_match or clrlwi_match:
      # Handle the case where the params are about to be modified on the next line.
      # It's ANDing the current params with an inverted form of their mask in order to zero out the param value in question.
      # In order to properly extract the param mask from this, we need to detect it before it happens and invert the mask.
      
      upcoming_stw_match = re.search(r" 	stw     (r\d+),(\d+)\((r\d+)\)", lines[line_index+1], re.IGNORECASE)
      upcoming_sth_match = re.search(r" 	sth     (r\d+),(\d+)\((r\d+)\)", lines[line_index+1], re.IGNORECASE)
      upcoming_stw_params_match = None
      upcoming_sth_aux_params_1_match = None
      upcoming_sth_aux_params_2_match = None
      
      if upcoming_stw_match:
        if all_registers[upcoming_stw_match.group(3)] == "entity":
          if upcoming_stw_match.group(2) == "176":
            upcoming_stw_params_match = upcoming_stw_match
        upcoming_stw_match = None
      if upcoming_sth_match:
        if all_registers[upcoming_sth_match.group(3)] == "entity":
          if upcoming_sth_match.group(2) in ["476", "516", "524"]:
            upcoming_sth_aux_params_1_match = upcoming_sth_match
          elif upcoming_sth_match.group(2) in ["480", "520", "528"]:
            upcoming_sth_aux_params_2_match = upcoming_sth_match
        upcoming_sth_match = None
      
      if upcoming_stw_params_match and curr_mask_attribute_name == "params":
        #print(line)
        should_invert_curr_mask = True
      elif upcoming_sth_aux_params_1_match and curr_mask_attribute_name == "aux_params_1":
        #print(line)
        should_invert_curr_mask = True
      elif upcoming_sth_aux_params_2_match and curr_mask_attribute_name == "aux_params_2":
        #print(line)
        should_invert_curr_mask = True
    
    
    mr_match = re.search(r" 	mr      (r\d+),(r\d+)", line, re.IGNORECASE)
    
    overwrite_register_match = re.search(r" 	(?:" + "|".join(ALL_OVERWRITING_OPCODES) + ")\.?\s+(r\d+),", line, re.IGNORECASE)
    bl_match = re.search(r" 	bl      0x[0-9a-f]+\s+;.+? {2,}(.+)$", line, re.IGNORECASE)
    start_symbol_match = re.search(r"^; SYMBOL: [0-9a-f]+\s+(.+)$", line, re.IGNORECASE)
    
    if prmabstract_match:
      num_bits_line = lines[line_index-2]
      bit_index_offset_line = lines[line_index-1]
      
      num_bits_match = re.search(r" 	li      (r\d+),(\d+)", num_bits_line)
      assert num_bits_match.group(1) == "r4"
      num_bits = int(num_bits_match.group(2))
      
      bit_index_offset_match = re.search(r" 	li      (r\d+),(\d+)", bit_index_offset_line)
      assert bit_index_offset_match.group(1) == "r5"
      bit_index_offset = int(bit_index_offset_match.group(2))
      
      bit_mask = (1 << num_bits) - 1
      bit_mask <<= bit_index_offset
      #curr_bit_masks_list["params"].append(bit_mask)
      add_mask_to_list(curr_bit_masks_list["params"], bit_mask, line, last_seen_symbol_name)
    elif lwz_params_match:
      all_registers[lwz_params_match.group(1)] = "params"
    elif lha_aux_params_1_match:
      all_registers[lha_aux_params_1_match.group(1)] = "aux_params_1"
    elif lha_aux_params_2_match:
      all_registers[lha_aux_params_2_match.group(1)] = "aux_params_2"
    elif rlwinm_match:
      bit_shift_amount = int(rlwinm_match.group(3))
      first_bit_index_msb_order = int(rlwinm_match.group(4))
      last_bit_index_msb_order = int(rlwinm_match.group(5))
      
      if last_bit_index_msb_order >= first_bit_index_msb_order:
        num_bits = (last_bit_index_msb_order - first_bit_index_msb_order) + 1
        rlwinm_mask = (1 << num_bits) - 1
        first_bit_index = (31 - last_bit_index_msb_order)
        rlwinm_mask <<= first_bit_index
      else:
        # A case like where the first bit comes after the last bit.
        # This results in the bits in the mask not being a single contiguous line.
        # e.g. "rlwinm  r0,r0,0,4,0" would result in the mask 0x8FFFFFFF.
        num_bits_right_half = (31 - first_bit_index_msb_order) + 1
        rlwinm_mask_right_half = (1 << num_bits_right_half) - 1
        
        num_bits_left_half = last_bit_index_msb_order + 1
        rlwinm_mask_left_half = (1 << num_bits_left_half) - 1
        rlwinm_mask_left_half <<= (31 - last_bit_index_msb_order)
        
        rlwinm_mask = rlwinm_mask_right_half | rlwinm_mask_left_half
      
      # Simulate rotating
      bit_mask = rlwinm_mask << (32 - bit_shift_amount)
      bit_mask = (bit_mask & 0xFFFFFFFF) | (bit_mask >> 32)
      
      if should_invert_curr_mask:
        bit_mask = (~bit_mask)
        if curr_mask_attribute_name == "params":
          bit_mask &= 0xFFFFFFFF
        else:
          bit_mask &= 0xFFFF
      
      #curr_bit_masks_list[curr_mask_attribute_name].append(bit_mask)
      add_mask_to_list(curr_bit_masks_list[curr_mask_attribute_name], bit_mask, line, last_seen_symbol_name)
      
      #print(line)
      #print("  %08X" % bit_mask)
      #print(first_bit_index_msb_order, last_bit_index_msb_order)
    elif clrlwi_match:
      first_shifted_bit_index = int(clrlwi_match.group(3))
      num_bits = (31 - first_shifted_bit_index) + 1
      
      bit_mask = (1 << num_bits) - 1
      
      if should_invert_curr_mask:
        bit_mask = (~bit_mask)
        if curr_mask_attribute_name == "params":
          bit_mask &= 0xFFFFFFFF
        else:
          bit_mask &= 0xFFFF
      
      #curr_bit_masks_list[curr_mask_attribute_name].append(bit_mask)
      add_mask_to_list(curr_bit_masks_list[curr_mask_attribute_name], bit_mask, line, last_seen_symbol_name)
      #print(line)
    elif stb_match:
      bit_mask = 0x000000FF
      #curr_bit_masks_list[curr_mask_attribute_name].append(bit_mask)
      add_mask_to_list(curr_bit_masks_list[curr_mask_attribute_name], bit_mask, line, last_seen_symbol_name)
    #elif sth_match:
    #  bit_mask = 0x0000FFFF
    #  #curr_bit_masks_list[curr_mask_attribute_name].append(bit_mask)
    #  add_mask_to_list(curr_bit_masks_list[curr_mask_attribute_name], bit_mask, line, last_seen_symbol_name)
    elif cmplwi_match or cmpw_match:
      if curr_mask_attribute_name == "params":
        bit_mask = 0xFFFFFFFF
      else:
        bit_mask = 0xFFFF
      #curr_bit_masks_list[curr_mask_attribute_name].append(bit_mask)
      add_mask_to_list(curr_bit_masks_list[curr_mask_attribute_name], bit_mask, line, last_seen_symbol_name)
    
    # Handle setting and clearing some registers
    if mr_match:
      dst_reg = mr_match.group(1)
      src_reg = mr_match.group(2)
      
      if all_registers[src_reg] == "params":
        all_registers[dst_reg] = "params"
      elif all_registers[src_reg] == "aux_params_1":
        all_registers[dst_reg] = "aux_params_1"
      elif all_registers[src_reg] == "aux_params_2":
        all_registers[dst_reg] = "aux_params_2"
      elif all_registers[src_reg] == "entity":
        all_registers[dst_reg] = "entity"
      else:
        all_registers[dst_reg] = None
    elif overwrite_register_match and not had_any_successful_load_match:
      all_registers[overwrite_register_match.group(1)] = None
    elif bl_match:
      # Handle overwriting registers when a function is called.
      func_name = bl_match.group(1)
      if func_name.startswith("_savegpr") or func_name.startswith("_restgpr"):
        # These functions preserve/restore registers at the start/end of a function.
        # So they don't overwrite registers.
        pass
      else:
        for i in range(0, 13+1):
          all_registers["r%d" % i] = None
          # Registers 14-31 aren't overwritten by function calls
    elif start_symbol_match:
      symbol_name = start_symbol_match.group(1)
      
      for i in range(0, 31+1):
        all_registers["r%d" % i] = None
      all_registers["r3"] = "entity"
      
      last_seen_symbol_name = symbol_name
  
  def print_all_bit_masks_for_class(bit_masks_by_attribute):
    result_string = ""
    result_string_with_code_lines = ""
    
    for param_attribute_name, masks in bit_masks_by_attribute.items():
      #masks = list(set(masks))
      masks.sort()
      for bit_mask, code_lines in masks:
        full_mask_except_this_one = 0
        for other_bit_mask, other_code_lines in masks:
          if bit_mask == other_bit_mask:
            continue
          full_mask_except_this_one |= other_bit_mask
        
        if param_attribute_name == "params":
          num_mask_digits = 8
        else:
          num_mask_digits = 4
        string = ("  %s & %0" + str(num_mask_digits) + "X") % (param_attribute_name, bit_mask)
        if bit_mask & full_mask_except_this_one != 0:
          string += " (WARNING: overlaps)"
        print(string)
        result_string += string + "\n"
        result_string_with_code_lines += string + "\n"
        
        for code_line in code_lines:
          print("    " + code_line)
          result_string_with_code_lines += "    " + code_line + "\n"
    
    return (result_string, result_string_with_code_lines)
  
  result_string, result_string_with_code_lines = print_all_bit_masks_for_class(all_bit_masks)
  final_output_string += result_string
  final_output_string_with_code_lines += result_string_with_code_lines
  
  if any(masks for attr, masks in all_bit_masks_for_subclass.items()):
    print("Params for possible subclass:")
    final_output_string += "Params for possible subclass:\n"
    final_output_string_with_code_lines += "Params for possible subclass:\n"
    result_string, result_string_with_code_lines = print_all_bit_masks_for_class(all_bit_masks_for_subclass)
    final_output_string += result_string
    final_output_string_with_code_lines += result_string_with_code_lines
  
  print()
  final_output_string += "\n"
  final_output_string_with_code_lines += "\n"

with open("./All entity parameter masks.txt", "w") as f:
  f.write(final_output_string)

with open("./All entity parameter masks - with code lines.txt", "w") as f:
  f.write(final_output_string_with_code_lines)
