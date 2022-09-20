from binascii import hexlify
from os import remove
from struct import pack
from apis.mii2studio.gen1_wii import CoreDataWii

def genRender(rkg_info):

    input_file = "tmp/tmp.miigx"

    with open(input_file,"wb") as wf:
        # 0xC3 Offset | 0x4A Length | Blocks 0xC3 to 0x85
        wf.write(rkg_info[60:60+74])

    input_type = "wii"
    vecchiofile = "tmp/a"

    orig_mii = CoreDataWii.from_file(input_file)

    def u8(data):
        return pack(">B", data)
        
    if "switch" not in input_type:
        if orig_mii.creator_name != "\0" * 10:
            pass
        if orig_mii.birth_month != 0 and orig_mii.birth_day != 0:
            pass

        favorite_colors = {
            0: "Red",
            1: "Orange",
            2: "Yellow",
            3: "Lime Green",
            4: "Forest Green",
            5: "Royal Blue",
            6: "Sky Blue",
            7: "Pink",
            8: "Purple",
            9: "Brown",
            10: "White",
            11: "Black"
        }

        mii_types = {
            0x00: "Special Mii - Gold Pants",
            0x20: "Normal Mii - Black Pants",
            0x40: "Special Mii - Gold Pants",
            0x60: "Normal Mii - Black Pants",
            0xC0: "Foreign Mii - Blue Pants (uneditable)",
            0xE0: "Normal Mii - Black Pants",
            0x100: "???"
        }
        
        if "switch" not in input_type:
            pass
        
        if "switch" not in input_type and input_type != "wii" and input_type != "ds":
            pass

        studio_mii = {}

        makeup = { # lookup table
            1: 1,
            2: 6,
            3: 9,
            9: 10
        }

        wrinkles = { # lookup table
            4: 5,
            5: 2,
            6: 3,
            7: 7,
            8: 8,
            10: 9,
            11: 11
        }

    # we generate the Mii Studio file by reading each Mii format from the Kaitai files.
    # unlike consoles which store Mii data in an odd number of bits,
    # all the Mii data for a Mii Studio Mii is stored as unsigned 8-bit integers. makes it easier.

        if "switch" not in input_type:
            if orig_mii.facial_hair_color == 0:
                studio_mii["facial_hair_color"] = 8
            else:
                studio_mii["facial_hair_color"] = orig_mii.facial_hair_color
        else:
            studio_mii["facial_hair_color"] = orig_mii.facial_hair_color
        studio_mii["beard_goatee"] = orig_mii.facial_hair_beard
        studio_mii["body_weight"] = orig_mii.body_weight
        if input_type == "wii" or input_type == "ds":
            studio_mii["eye_stretch"] = 3
        else:
            studio_mii["eye_stretch"] = orig_mii.eye_stretch
        if "switch" not in input_type:
            studio_mii["eye_color"] = orig_mii.eye_color + 8
        else:
            studio_mii["eye_color"] = orig_mii.eye_color
        studio_mii["eye_rotation"] = orig_mii.eye_rotation
        studio_mii["eye_size"] = orig_mii.eye_size
        studio_mii["eye_type"] = orig_mii.eye_type
        studio_mii["eye_horizontal"] = orig_mii.eye_horizontal
        studio_mii["eye_vertical"] = orig_mii.eye_vertical
        if input_type == "wii" or input_type == "ds":
            studio_mii["eyebrow_stretch"] = 3
        else:
            studio_mii["eyebrow_stretch"] = orig_mii.eyebrow_stretch
        if "switch" not in input_type:
            if orig_mii.eyebrow_color == 0:
                studio_mii["eyebrow_color"] = 8
            else:
                studio_mii["eyebrow_color"] = orig_mii.eyebrow_color
        else:
            studio_mii["eyebrow_color"] = orig_mii.eyebrow_color
        studio_mii["eyebrow_rotation"] = orig_mii.eyebrow_rotation
        studio_mii["eyebrow_size"] = orig_mii.eyebrow_size
        studio_mii["eyebrow_type"] = orig_mii.eyebrow_type
        studio_mii["eyebrow_horizontal"] = orig_mii.eyebrow_horizontal
        if input_type != "switchdb":
            studio_mii["eyebrow_vertical"] = orig_mii.eyebrow_vertical
        else:
            studio_mii["eyebrow_vertical"] = orig_mii.eyebrow_vertical + 3
        studio_mii["face_color"] = orig_mii.face_color
        if input_type == "wii" or input_type == "ds":
            if orig_mii.facial_feature in makeup:
                studio_mii["face_makeup"] = makeup[orig_mii.facial_feature]
            else:
                studio_mii["face_makeup"] = 0
        else:
            studio_mii["face_makeup"] = orig_mii.face_makeup
        studio_mii["face_type"] = orig_mii.face_type
        if input_type == "wii" or input_type == "ds":
            if orig_mii.facial_feature in wrinkles:
                studio_mii["face_wrinkles"] = wrinkles[orig_mii.facial_feature]
            else:
                studio_mii["face_wrinkles"] = 0
        else:
            studio_mii["face_wrinkles"] = orig_mii.face_wrinkles
        studio_mii["favorite_color"] = orig_mii.favorite_color
        studio_mii["gender"] = orig_mii.gender
        if "switch" not in input_type:
            if orig_mii.glasses_color == 0:
                studio_mii["glasses_color"] = 8
            elif orig_mii.glasses_color < 6:
                studio_mii["glasses_color"] = orig_mii.glasses_color + 13
            else:
                studio_mii["glasses_color"] = 0
        else:
            studio_mii["glasses_color"] = orig_mii.glasses_color
        studio_mii["glasses_size"] = orig_mii.glasses_size
        studio_mii["glasses_type"] = orig_mii.glasses_type
        studio_mii["glasses_vertical"] = orig_mii.glasses_vertical
        if "switch" not in input_type:
            if orig_mii.hair_color == 0:
                studio_mii["hair_color"] = 8
            else:
                studio_mii["hair_color"] = orig_mii.hair_color
        else:
            studio_mii["hair_color"] = orig_mii.hair_color
        studio_mii["hair_flip"] = orig_mii.hair_flip
        studio_mii["hair_type"] = orig_mii.hair_type
        studio_mii["body_height"] = orig_mii.body_height
        studio_mii["mole_size"] = orig_mii.mole_size
        studio_mii["mole_enable"] = orig_mii.mole_enable
        studio_mii["mole_horizontal"] = orig_mii.mole_horizontal
        studio_mii["mole_vertical"] = orig_mii.mole_vertical
        if input_type == "wii" or input_type == "ds":
            studio_mii["mouth_stretch"] = 3
        else:
            studio_mii["mouth_stretch"] = orig_mii.mouth_stretch
        if "switch" not in input_type:
            if orig_mii.mouth_color < 4:
                studio_mii["mouth_color"] = orig_mii.mouth_color + 19
            else:
                studio_mii["mouth_color"] = 0
        else:
            studio_mii["mouth_color"] = orig_mii.mouth_color
        studio_mii["mouth_size"] = orig_mii.mouth_size
        studio_mii["mouth_type"] = orig_mii.mouth_type
        studio_mii["mouth_vertical"] = orig_mii.mouth_vertical
        studio_mii["beard_size"] = orig_mii.facial_hair_size
        studio_mii["beard_mustache"] = orig_mii.facial_hair_mustache
        studio_mii["beard_vertical"] = orig_mii.facial_hair_vertical
        studio_mii["nose_size"] = orig_mii.nose_size
        studio_mii["nose_type"] = orig_mii.nose_type
        studio_mii["nose_vertical"] = orig_mii.nose_vertical

    with open(vecchiofile, "wb") as f:
        mii_data_bytes = ""
        mii_data = b""
        n = r = 256
        mii_dict = []
        if input_type == "miistudio":
            with open(input_file, "rb") as g:
                read = g.read()
                g.close()
            
            for i in range(0, len(hexlify(read)), 2):
                mii_dict.append(int(hexlify(read)[i:i+2], 16))
        else:
            mii_dict = studio_mii.values()
    #    mii_data_bytes += hexlify(u8(0))
        mii_data += hexlify(u8(0))
        for v in mii_dict:
            eo = (7 + (v ^ n)) % 256 # encode the Mii, Nintendo seemed to have randomized the encoding using Math.random() in JS, but we removed randomizing
            n = eo
    #        mii_data_bytes += hexlify(u8(mii_dict))
            mii_data += hexlify(u8(eo))
            f.write(u8(v))
            mii_data_bytes += str(hexlify(u8(v)), "ascii")

        f.close()
        
        #codecs.decode(mii_data_bytes, "hex")
        #mii_data_bytes = mii_data_bytes.decode("utf-8")

        remove(vecchiofile)
        return "=IMAGE(\"https://studio.mii.nintendo.com/miis/image.png?data=" + mii_data.decode("utf-8") + "&type=face&width=512\")"