
import glob
import re

#all_asm_files = glob.glob('./rels/*.asm')
#all_asm_files += ["main.asm"]
all_asm_files = glob.glob("../../disassemble/*.asm")

EVENT_BIT_FUNCTIONS = [
  "dSv_event_c::onEventBit(unsigned short)",
  "dSv_event_c::offEventBit(unsigned short)",
  "dSv_event_c::isEventBit(unsigned short)",
  "dSv_event_c::setEventReg(unsigned short, unsigned char)",
  "dSv_event_c::getEventReg(unsigned short)",
  "JAIZelBasic::checkEventBit(unsigned short)",
  "dComIfGs_onEventBit(unsigned short)",
  "dComIfGs_isEventBit(unsigned short)",
  "dComIfGs_getEventReg(unsigned short)",
]

found_event_bits = [
  0x3040, 0x2E02, 0x0902, 0x0A02, 0x0A20, 0x2E04, 0x2A08, # these are checked by dComIfGs_checkSeaLandingEvent__FSc
  0x2A08, 0x0F80, 0x0801, 0x0808, 0x2401, # these are checked by dComIfGs_setGameStartStage__Fv
  0x95FF, 0x94FF, 0x93FF, 0x92FF, 0x91FF, 0x90FF, 0x8FFF, 0x8EFF, 0x8DFF,
    0x8CFF, 0xB1FF, 0x9CFF, 0x84FF, 0x83FF, 0x82FF, 0x81FF, 0x80FF, # these are checked by reinit__10dSv_info_cFv
  0x1008, 0x1004, # checked by auction
  0x3020, 0x3010, 0x3008, 0x3004, 0x3002, 0x3001, 0x3180, # checked by bigelf
  0xF8FF, 0xF7FF, 0xF6FF, 0xF5FF, 0xF4FF, 0xF3FF, 0xF2FF, 0xF1FF, 0xF0FF,
    0xEFFF, 0xEEFF, 0xEDFF, 0xECFF, 0xEBFF, 0xEAFF, 0xE9FF, 0xE8FF, 0xE7FF, 0xE6FF,
    0xE5FF, 0xE4FF, 0xE3FF, 0xE2FF, 0xE1FF, 0xE0FF, 0xDFFF, 0xDEFF, 0xDDFF, 0xDCFF,
    0xDBFF, 0xDAFF, 0xD9FF, 0xD8FF, 0xD7FF, 0xD6FF, 0xD5FF, 0xD4FF, 0xD3FF, 0xD2FF, 0xD1FF, # listed in m_savelabel__7daDai_c
  0x9AFF, 0x99FF, 0x9EFF, 0x98FF, 0x96FF, 0x97FF, # checked by d_a_npc_bj1
  0x95FF, 0x94FF, 0x93FF, 0x92FF, 0x91FF, 0x90FF, 0x8FFF, 0x8EFF, 0x8DFF,
    0x8CFF, 0xB1FF, 0x9CFF, 0x84FF, 0x83FF, 0x82FF, 0x81FF, 0x80FF, # checked by d_a_npc_mt
  0xF8FF, 0xF7FF, 0xF6FF, 0xF5FF, 0xF4FF, 0xF3FF, # d_a_npc_people
  0x1701, 0x1601, 0xC407, # checked by npc_photo
  0x2080, 0x2004, 0x2002, 0x2804, 0x2802, 0x2801,
    0x2980, 0x2940, 0x3B01, 0x3C80, 0x3C40, 0x3C20, 0x3C10, 0x3C08, 0x3C04, 0x3C02, # m_savelabel__11daSalvage_c, d_a_salvage
  0xAC03, 0xB503, 0x7D03, 0x7B03, 0x9D03, 0x7A03, 0xB203,
    0x8B03, 0xAC03, 0xB003, 0xAE03, 0x7C03, 0xAF03, # toripost
  0xA207, 0xA107, 0xA007, 0x9F07, 0xA307, 0xA407, # dungeon warp jars (warpt)
  0x0902, 0x0A20, 0x0A02, 0x1F04, 0x2E04, 0x2E02, 0x3E10,  # d_a_tag_island
  0x95FF, 0x94FF, 0x93FF, 0x92FF, 0x91FF, 0x90FF, 0x8FFF,
    0x8EFF, 0x8DFF, 0x8CFF, 0xB1FF, 0x9CFF, 0x84FF, 0x83FF, 0x82FF, 0x81FF, 0x80FF, # d_a_obj_figure
  0x1320, 0x1310, 0x1308, # d_a_npc_roten (checked bits)
  0x1304, 0x1302, 0x1301, # d_a_npc_roten (set bits)
  0xCB03, 0xCA03, 0xC903, # d_a_npc_roten (checked regs)
  0x2920, 0x2910, # d_a_tag_md_cb
  0x3904, 0x3902, 0x3901, 0x3A80, 0x3240, 0x3220, 0x3210, 0x3208, # d_a_obj_vgnfd
  0x2910, 0x2920, # d_a_obj_mknjd
  0x3508, 0x3504, 0x3502, 0x3501, 0x3680, 0x3640, 0x3620, 0x3610,
    0x3608, 0x3604, 0x3602, 0x3601, 0x3780, 0x3740, 0x3720, 0x3710, # d_a_obj_adnno
  0x0008, 0x0004, 0x0010, # d_a_npc_uk
  0x1202, 0x1204, 0x1201, # d_a_npc_uk
  0x0180, 0x0140, 0x0001, # d_a_npc_uk
  0x1240, 0x1D08, 0x1D04, 0x1D02, 0x1D01, # d_a_npc_tc
  0x0E40, 0x0E80, 0x1C20, # d_a_npc_de1
  0x0702, 0x1502, 0x0940, 0x0704, 0x0701, # d_a_npc_p2
  0xBA0F, # stringSet__21fopMsgM_msgDataProc_cFv and stringLength__21fopMsgM_msgDataProc_cFv
  0x0420, # new_himo2_move__FP11himo2_class
  0x0540, 0x0580, 0x0420, # new_himo2_move__FP11himo2_class
  0x2D10, 0x2D08, 0x3280, 0x2E80, 0x2E80, 0x2E80, 0x2D40,
    0x2D20, 0x3B02, 0x4002, 0x3F40, 0x3B08, 0x4004, 0x2D02,
    0x2D04, 0x3A04, 0x3910, 0x2D01, 0x2580, 0x3A02, 0x2110,
    0x3920, 0x2401, 0x1001, 0x1001, 0x3B10, 0x2E01, 0x2E01, # STB cutscenes set event flags sometimes
]

log = []
for asm_file in all_asm_files:
  print(asm_file)
  with open(asm_file) as f:
    lines = f.read().splitlines()
  
  last_r3_value = None
  last_r4_value = None
  for line in lines:
    #print(line)
    
    for event_bit_function in EVENT_BIT_FUNCTIONS:
      if line.strip().endswith(event_bit_function):
        if event_bit_function.startswith("dComIfGs"):
          last_reg_value = last_r3_value
        else:
          last_reg_value = last_r4_value
        if last_reg_value: # Ignore values we don't understand. TODO
          found_event_bits.append(last_reg_value)
          
          #print("Event: %04X" % last_reg_value)
          log.append("File: %s" % asm_file)
          log.append("Line: %s" % line)
          log.append("Event: %04X" % last_reg_value)
          log.append("")
        else:
          pass#print("Unknown: %s" % line)
        break
    
    r3_li_match = re.search(r"li      r3,(\d+)", line)
    r3_addi_match = re.search(r"addi    r3,r3,-(\d+)", line)
    r3_mr_match = re.search(r"mr      r3,r\d+", line)
    if r3_li_match:
      last_r3_value = int(r3_li_match.group(1))
    elif r3_addi_match:
      last_r3_value = (-int(r3_addi_match.group(1)))&0xFFFF
    elif r3_mr_match or line.endswith("blr"):
      last_r3_value = None
    
    r4_li_match = re.search(r"li      r4,(\d+)", line)
    r4_addi_match = re.search(r"addi    r4,r4,-(\d+)", line)
    r4_mr_match = re.search(r"mr      r4,r\d+", line)
    if r4_li_match:
      last_r4_value = int(r4_li_match.group(1))
    elif r4_addi_match:
      last_r4_value = (-int(r4_addi_match.group(1)))&0xFFFF
    elif r4_mr_match or line.endswith("blr"):
      last_r4_value = None

#exit()

found_event_bits = list(set(found_event_bits))
found_event_bits.sort()
for event_bit in found_event_bits:
  print("%04X" % event_bit)

bytes = []
for i in range(0, 0xFF+1):
  bytes.append(0)
for event_bit in found_event_bits:
  bits = event_bit&0xFF
  offset = (event_bit&0xFF00)>>8
  bytes[offset] |= bits
output_str = ""
for i in range(0, 0xFF+1):
  byte = bytes[i]
  str = "%02X:  %02X" % (i, byte)
  print(str)
  output_str += str + "\n"
with open("Used event bits.txt", "w") as f:
  f.write(output_str)

with open("Used event bits log.txt", "w") as f:
  for line in log:
    f.write(line + "\n")
