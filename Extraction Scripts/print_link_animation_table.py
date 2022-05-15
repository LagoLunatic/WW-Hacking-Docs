
with open("Link Animation Data Table (Indexes).txt", "w") as f:
  f.write("Anim: Upper Under   L  R   Tex\n")
  for i in range(0xEA):
    addr = 0x8035C764 + i*8
    upper_anim = self.dol.read_data(read_u16, addr + 0x00)
    under_anim = self.dol.read_data(read_u16, addr + 0x02)
    left_hand = self.dol.read_data(read_u8, addr + 0x04)
    right_hand = self.dol.read_data(read_u8, addr + 0x05)
    texture_anim = self.dol.read_data(read_u16, addr + 0x06)
    f.write("  %02X:  %04X  %04X  %02X %02X  %04X\n" % (i, upper_anim, under_anim, left_hand, right_hand, texture_anim))

with open("Link Animation Data Table (Names).txt", "w") as f:
  f.write("% 4s:  % 21s  % 21s  % 2s % 2s  %21s %21s\n" % ("Anim", "Upper Body", "Lower Body", "L", "R", "Texture Swap", "Texture SRT"))
  lkanm = self.get_arc("files/res/Object/LkAnm.arc")
  for i in range(0xEA):
    addr = 0x8035C764 + i*8
    upper_anim = self.dol.read_data(read_u16, addr + 0x00)
    under_anim = self.dol.read_data(read_u16, addr + 0x02)
    left_hand = self.dol.read_data(read_u8, addr + 0x04)
    right_hand = self.dol.read_data(read_u8, addr + 0x05)
    texture_anim = self.dol.read_data(read_u16, addr + 0x06)
    upper_name = lkanm.file_entries[upper_anim].name
    under_name = lkanm.file_entries[under_anim].name
    
    texture_addr = 0x8035C36C + texture_anim*4
    btp_anim = self.dol.read_data(read_u16, texture_addr + 0x00)
    btk_anim = self.dol.read_data(read_u16, texture_addr + 0x02)
    btp_name = lkanm.file_entries[btp_anim].name
    btk_name = lkanm.file_entries[btk_anim].name
    
    f.write("  %02X:  % 21s  % 21s  %02X %02X  %21s %21s\n" % (i, upper_name, under_name, left_hand, right_hand, btp_name, btk_name))
