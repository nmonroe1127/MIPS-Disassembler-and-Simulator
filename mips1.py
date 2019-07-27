import sys
import struct


instructions = [None ] * 500 
address =  [None ] * 500
rs = [None ] * 500
rt = [None ] * 500
rd = [None ] * 500
imm =  [None ] * 500
sa = [None ] * 500
func =  [None ] * 500
op = [None ] * 500
inv = [None ] * 500

def dissassemble():
    # how to read binary file and get ints
    inFile = open( sys.argv[2], 'rb' )	
    try:
        outFile = open(sys.argv[4] + "_dis.txt", "a")
    except IOError:
        outFile = open(sys.argv[4] + "_dis.txt", "w")

    addr = 96
    break_flag = False
    no_sim = False
    bltz_flag = 0
    list_of_ins = []
    data = []

    while True :
            bitsInStrForm = inFile.read(4)
            if len( bitsInStrForm) == 0 :
                break

            address[addr] = addr 

            instructions[addr] =  struct.unpack('>I', bitsInStrForm)[0] 
            
            # go ahead and get the 16 bit IMM out form the binary
            # this is the easiest way to do it.
            imm[ addr ]   = struct.unpack('>h', bitsInStrForm[2:4])[0]

            # use I to hold the current instruction
            I = instructions[ addr ]
            # get IMMEDIATE bits

            # get the opcode bits
            op[addr] = I>>26

            binstr = bin(I)
            # get the opcode bits
            op[addr] = I>>26
            # get the RS bits
            inv[addr] = I>>31
            rs[ addr] = ((I<<6) & 0xFFFFFFFF) >> 27
            rt[ addr] = ((I<<11)& 0xFFFFFFFF) >> 27
            rd[ addr] = ((I<<16)& 0xFFFFFFFF) >> 27
            #get the binary output formatted
            if break_flag == False:
                binstr = bin(I)
                binstr = '0'* (32 - len( binstr[2:] )) + binstr[2:] 
                binstr = binstr[0] + ' ' + binstr[1:6] + ' ' + binstr[6:11] \
                        + ' ' + binstr[11:16] + ' ' + binstr[16:21] \
                        + ' ' + binstr[21:26] + ' ' + binstr[26:32]
                outFile.write(binstr)

                if inv[addr] ==0 :
                    operation = "Invalid"
                    print >> outFile,  '\t', addr, '\tInvalid Instruction'
                    no_sim = True 
                elif op[addr] == 40:
                    operation = "ADDI"
                    print >> outFile, '\t', addr, '\tADDI \tR', rt[addr], ', R', rs[addr], ', #', imm[addr]
                elif op[addr] == 43:
                    operation = "SW"
                    print >> outFile, '\t', addr, '\tSW \tR', rt[addr], ',', imm[addr], '(R', rs[addr], ')'
                elif op[addr] == 35:
                    operation = "LW"
                    print >> outFile, '\t', addr, '\tLW \tR', rt[addr], ',', imm[addr], '(R', rs[addr], ')'
                elif op[addr] == 33:
                    operation = "BLTZ"
                    print >> outFile, '\t', addr, '\tBLTZ \tR', rs[addr], ', #', imm[addr]*4
                elif op[addr] == 60:
                    operation = "MUL"
                    print >> outFile, '\t', addr, '\tMUL \tR', rd[addr], ', R', rs[addr], ', R', rt[addr]
                elif I == 2147483648:
                    operation = "NOP"
                    print >> outFile, '\t', addr, '\tNOP'
                elif op[addr] == 32:
                    if binstr[32:39] == '000000':
                        operation = "SLL"
                        print >> outFile, '\t', addr, '\tSLL \tR', rd[addr], ', R', rt[addr], ', #', int(binstr[25:31], 2)
                    elif binstr[32:39] == '100010':
                        operation = "SUB"
                        print >> outFile, '\t', addr, '\tSUB \tR', rd[addr], ', R', rs[addr], ', R', rt[addr]
                    elif binstr[32:39] == '100000':
                        operation = "ADD"
                        print >> outFile, '\t', addr, '\tADD \tR', rd[addr], ', R', rs[addr], ', R', rt[addr]
                    elif binstr[32:39] == '001000':
                        operation = "JR"
                        print >> outFile, '\t', addr, '\tJR \tR', rs[addr]
                    elif binstr[32:39] == '000010':
                        operation = "SRL"
                        print >> outFile, '\t', addr, '\tSRL \tR', rd[addr], ', R', rt[addr], ', #', inv[addr]
                    elif binstr[32:39] == '001010':
                        operation = "MOVZ"
                        print >> outFile, '\t', addr, '\tMOVZ \tR', rd[addr], ', R', rs[addr], ', R', rt[addr]
                    else:
                        operation = "BREAK"
                        print >> outFile, '\t', addr, '\tBREAK'
                        break_flag = True      
                elif op[addr] == 34:
                    operation = "J"
                    print >> outFile, '\t', addr, '\tJ \t#', imm[addr]*4
                else:
                    operation = "IDK"
                    print >> outFile, '\t', addr

                list_of_ins.append({'addr': addr, 'operation': operation, 'rd':rd[addr], 'rt':rt[addr],
                                    'inv': inv[addr], 'rs':rs[addr], 'imm':imm[addr], 'binstr': binstr})

            else:
                binstr = bin(I)
                binstr = '0'* (32 - len( binstr[2:] )) + binstr[2:]
                print >> outFile, binstr,
                print >> outFile, '\t', addr, '\t', twos_comp(int(binstr,2), 32)
                data.append({'addr':addr, 'twos':twos_comp(int(binstr,2), 32)})
            
            
            addr += 4

    sim_count = 1
    simulation(sim_count, list_of_ins, data)

    inFile.close()
    outFile.close()
    # Dissassembly finished

def simulation(count, list_of_ins, data):
    sim_flag = True
    j_flag = False
    address_flag = True
    i = 0
    d = 0
    register = 0
    running_ins = list_of_ins[i]
    register_value = [0,0,0,0,0,0,0,0,
                      0,0,0,0,0,0,0,0,
                      0,0,0,0,0,0,0,0,
                      0,0,0,0,0,0,0,0]

    final_data_address = data[len(data)-1]
    first_data_address = data[0]
    data_range = (final_data_address['addr'] - first_data_address['addr'] + 4)/4
    running_range = 0
    full_running_range = 0

    while sim_flag == True:
        try:
            simFile = open(sys.argv[4] + "_sim.txt", "a")
        except IOError:
            simFile = open(sys.argv[4] + "_sim.txt", "w")

        if running_ins['operation'] == "Invalid":
            i += 1
            running_ins = list_of_ins[i]
        
        rt = running_ins['rt']
        rd = running_ins['rd']
        rs = running_ins['rs']
        binstr = running_ins['binstr']
        imm = running_ins['imm']
        operation = running_ins['operation']
        addr = running_ins['addr']



        print >> simFile, "===================="
        print >> simFile, "cycle:", count, 
        print >> simFile, addr, operation,

        if operation == "ADDI":
            print >> simFile, 'R', rt, ', R', rs, ', #', imm, '\n'
            register_value[running_ins['rt']] = register_value[rs] + imm
            i += 1
            running_ins = list_of_ins[i]
        elif operation == "SW":
            print >> simFile, 'R', rt, ',', imm, '(R', rs, ')', '\n'
            new_address = imm + register_value[rs]
            data_transfer_value = register_value[rt]
            for x in data:
                if x['addr'] == new_address:
                    x['twos'] = data_transfer_value
            i += 1
            running_ins = list_of_ins[i] 

        elif operation == "LW":
            print >> simFile, 'R', rt, ',', imm, '(R', rs, ')', '\n'
            for x in data:
                if x['addr'] == imm:
                    real_x = x['addr'] + register_value[rs]

            for n in data:
                if n['addr'] == real_x:
                    register_value[running_ins['rt']] = n['twos'] 

            i += 1
            running_ins = list_of_ins[i] 

        elif operation == "BLTZ":
            print >> simFile, 'R', rs, ', #', imm*4, '\n'
            for x in data:
                if x['addr'] == imm*4:
                    register_value[running_ins['rt']] = x['twos'] 
            if register_value[running_ins['rs']] < 0:
                i += 2
            i += 1
            running_ins = list_of_ins[i]
            final_bltz = data[len(data)-1]
            if final_bltz['twos'] < 0:
                running_ins = list_of_ins[len(list_of_ins)-1]
                
            

        elif operation == "SLL":
            print >> simFile, 'R', rd, ', R', rt, ', #', int(binstr[25:31], 2), '\n'
            if int(binstr[25:31], 2) == 1:
                data_multiplier = int(binstr[25:31], 2) + 1
            else:
                data_multiplier = 4
            register_value[running_ins['rd']] = register_value[running_ins['rt']]*(data_multiplier)
            i += 1
            running_ins = list_of_ins[i] 
            
        elif operation == "SUB":
            print >> simFile, 'R', rd, ', R', rs, ', R', rt, '\n'
            register_value[running_ins['rd']] = register_value[rs] - register_value[rt]
            i += 1
            running_ins = list_of_ins[i]   
        
        elif operation == "J":
            j_flag = True
            print >> simFile, '\t#', imm*4, '\n'
            position = 0
            address_pos = imm*4
            for x in list_of_ins:
                if x['addr'] == address_pos:
                    running_ins = list_of_ins[position]
                    i = position
                else:
                    position += 1

        elif operation == "JR":
            print >> simFile, 'R', rs, '\n'
            i += 1
            running_ins = list_of_ins[i]

        elif operation == "BREAK":
            sim_flag = False
            print >> simFile, '\n'

        elif operation == "ADD":
            print >> simFile, 'R', rd, ', R', rs, ', R', rt, '\n'
            register_value[running_ins['rd']] = register_value[rs] + register_value[rt]
            i += 1
            running_ins = list_of_ins[i] 

        elif operation == "MUL":
            print >> simFile, 'R', rd, ', R', rs, ', R', rt, '\n'
            register_value[running_ins['rd']] = register_value[rs] * register_value[rt]
            i += 1
            running_ins = list_of_ins[i]
        
        elif operation == "SRL":
            print >> simFile, 'R', rd, ', R', rt, ', #', int(binstr[25:31], 2), '\n'
            register_value[running_ins['rd']] = register_value[rt]/(int(binstr[25:31], 2) + 1)
            i += 1
            running_ins = list_of_ins[i]

        elif operation == "MOVZ":
            print >> simFile, 'R', rd, ', R', rs, ', R', rt, '\n'
            register_value[rd] = register_value[rs]+register_value[rt]
            i += 1
            running_ins = list_of_ins[i]

        elif operation == "NOP":
            print >> simFile, '\n'
            i += 1
            running_ins = list_of_ins[i]

        print >> simFile, "registers:"
        print >> simFile, "r00:",
        while register < 8:
            if register_value[register] != 0:
                print >> simFile, "\t", register_value[register],
            else:
                print >> simFile, "\t0",
            register += 1   
        print >> simFile, "\n",
        print >> simFile, "r08:",
        while register < 16:
            if register_value[register] != 0:
                print >> simFile, "\t", register_value[register],
            else:
                print >> simFile, "\t0",
            register += 1
        print >> simFile, "\n",
        print >> simFile, "r16:",
        while register < 24:
            if register_value[register] != 0:
                print >> simFile, "\t", register_value[register],
            else:
                print >> simFile, "\t0",
            register += 1
        print >> simFile, "\n",
        print >> simFile, "r24:",
        while register < 32:
            if register_value[register] != 0:
                print >> simFile, "\t", register_value[register],
            else:
                print >> simFile, "\t0",
            register += 1
        print >> simFile, "\n"
            
        register = 0

        print >> simFile, "data:"
        data_address = first_data_address
        
        while full_running_range <= data_range - 1:
            print >> simFile, data_address['addr'], ":",
            while running_range < 8 and full_running_range <= data_range:
                if data_address['twos'] == 4 and address_flag == True:
                    print >> simFile, '\t', data_address['twos'],
                    address_flag = False
                if address_flag == True:
                    print >> simFile, '\t', data_address['twos'],
                if d < data_range-1:
                    d += 1
                    data_address = data[d]
                full_running_range += 1
                running_range += 1
            print >> simFile, "\n",
            running_range = 0

        running_range = 0
        full_running_range = 0
        d = 0
        address_flag = True

        
        if sim_flag == True:
            print >> simFile, "\n",
        count = count + 1
    simFile.close()

def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0:
        val = val - (1 << bits)    
    return val 

if __name__ == '__main__':
    dissassemble()


