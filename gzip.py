# Author: Marco Simoes
# Adapted from Java's implementation of Rui Pedro Paiva
# Teoria da Informacao, LEI, 2022

import sys
from huffmantree import HuffmanTree



class GZIPHeader:
    ''' class for reading and storing GZIP header fields '''

    ID1 = ID2 = CM = FLG = XFL = OS = 0
    MTIME = []
    lenMTIME = 4
    mTime = 0

	# bits 0, 1, 2, 3 and 4, respectively (remaining 3 bits: reserved)
    FLG_FTEXT = FLG_FHCRC = FLG_FEXTRA = FLG_FNAME = FLG_FCOMMENT = 0   
	
	# FLG_FTEXT --> ignored (usually 0)
	# if FLG_FEXTRA == 1
    XLEN, extraField = [], []
    lenXLEN = 2
	
	# if FLG_FNAME == 1
    fName = ''  # ends when a byte with value 0 is read
	
	# if FLG_FCOMMENT == 1
    fComment = ''   # ends when a byte with value 0 is read
		
	# if FLG_HCRC == 1
    HCRC = []
		
		
	
    def read(self, f):
        ''' reads and processes the Huffman header from file. Returns 0 if no error, -1 otherwise '''

		# ID 1 and 2: fixed values
        self.ID1 = f.read(1)[0]  
        if self.ID1 != 0x1f: return -1 # error in the header
			
        self.ID2 = f.read(1)[0]
        if self.ID2 != 0x8b: return -1 # error in the header
		
		# CM - Compression Method: must be the value 8 for deflate
        self.CM = f.read(1)[0]
        if self.CM != 0x08: return -1 # error in the header
					
		# Flags
        self.FLG = f.read(1)[0]
		
		# MTIME
        self.MTIME = [0]*self.lenMTIME
        self.mTime = 0
        for i in range(self.lenMTIME):
            self.MTIME[i] = f.read(1)[0]
            self.mTime += self.MTIME[i] << (8 * i) 				
						
		# XFL (not processed...)
        self.XFL = f.read(1)[0]
		
		# OS (not processed...)
        self.OS = f.read(1)[0]
		
		# --- Check Flags
        self.FLG_FTEXT = self.FLG & 0x01
        self.FLG_FHCRC = (self.FLG & 0x02) >> 1
        self.FLG_FEXTRA = (self.FLG & 0x04) >> 2
        self.FLG_FNAME = (self.FLG & 0x08) >> 3
        self.FLG_FCOMMENT = (self.FLG & 0x10) >> 4
					
		# FLG_EXTRA
        if self.FLG_FEXTRA == 1:
			# read 2 bytes XLEN + XLEN bytes de extra field
			# 1st byte: LSB, 2nd: MSB
            self.XLEN = [0]*self.lenXLEN
            self.XLEN[0] = f.read(1)[0]
            self.XLEN[1] = f.read(1)[0]
            self.xlen = self.XLEN[1] << 8 + self.XLEN[0]
			
			# read extraField and ignore its values
            self.extraField = f.read(self.xlen)
		
        def read_str_until_0(f):
            s = ''
            while True:
                c = f.read(1)[0]
                if c == 0: 
                    return s
                s += chr(c)
		
		# FLG_FNAME
        if self.FLG_FNAME == 1:
            self.fName = read_str_until_0(f)
		
		# FLG_FCOMMENT
        if self.FLG_FCOMMENT == 1:
            self.fComment = read_str_until_0(f)
		
		# FLG_FHCRC (not processed...)
        if self.FLG_FHCRC == 1:
            self.HCRC = f.read(2)
			
        return 0
			



class GZIP:
    ''' class for GZIP decompressing file (if compressed with deflate) '''

    gzh = None
    gzFile = ''
    fileSize = origFileSize = -1
    numBlocks = 0
    f = None
	

    bits_buffer = 0
    available_bits = 0		

    
    def __init__(self, filename):
        self.gzFile = filename
        self.f = open(filename, 'rb')
        self.f.seek(0,2)
        self.fileSize = self.f.tell()
        self.f.seek(0)

		
	

    def decompress(self):
        ''' main function for decompressing the gzip file with deflate algorithm '''
		
        numBlocks = 0

		# get original file size: size of file before compression
        origFileSize = self.getOrigFileSize()
        print(origFileSize)
		
		# read GZIP header
        error = self.getHeader()
        if error != 0:
            print('Formato invalido!')
            return
		
		# show filename read from GZIP header
        print(self.gzh.fName)
        
        # MAIN LOOP - decode block by block
        BFINAL = 0	
        while not BFINAL == 1:	
            BFINAL = self.readBits(1)
            BTYPE = self.readBits(2)					
            if BTYPE != 2:
                print('Error: Block %d not coded with Huffman Dynamic coding' % (numBlocks+1))
                return
			
									
			#--- STUDENTS --- ADD CODE HERE
			# 
			#
            
            HLIT = self.readBits(5)
            HDIST = self.readBits(5)
            HCLEN = self.readBits(4)
            
            print(HLIT)
            print(HDIST)
            print(HCLEN)
            
            HCLEN_comp=self.comp_codigo(HCLEN+4)
            HCLEN_code=self.Huff_code(HCLEN_comp)
            HCLEN_tree=self.Huff_tree(HCLEN_code)
            
            HLIT_comp=self.comp(HCLEN_tree, HLIT+257)
            HLIT_code=self.Huff_code(HLIT_comp)
            HLIT_tree=self.Huff_tree(HLIT_code)
            
            HDIST_comp=self.comp(HCLEN_tree, HDIST+1)
            HDIST_code=self.Huff_code(HDIST_comp)
            HDIST_tree=self.Huff_tree(HDIST_code)
            
            data=self.decode_data(HLIT_tree, HDIST_tree)
            
            self.load_file(data)
            																																						
			# update number of blocks read
            numBlocks += 1
		

		
		# close file			
		
        self.f.close()	
        print("End: %d block(s) analyzed." % numBlocks)
	
	
    def getOrigFileSize(self):
        ''' reads file size of original file (before compression) - ISIZE '''
		
		# saves current position of file pointer
        fp = self.f.tell()
		
		# jumps to end-4 position
        self.f.seek(self.fileSize-4)
		
		# reads the last 4 bytes (LITTLE ENDIAN)
        sz = 0
        for i in range(4): 
            sz += self.f.read(1)[0] << (8*i)
		
		# restores file pointer to its original position
        self.f.seek(fp)
		
        return sz		
	

	
    def getHeader(self):  
        ''' reads GZIP header'''

        self.gzh = GZIPHeader()
        header_error = self.gzh.read(self.f)
        return header_error
		

    def readBits(self, n, keep=False):
        ''' reads n bits from bits_buffer. if keep = True, leaves bits in the buffer for future accesses '''

        while n > self.available_bits:
            self.bits_buffer = self.f.read(1)[0] << self.available_bits | self.bits_buffer
            self.available_bits += 8
		
        mask = (2**n)-1
        value = self.bits_buffer & mask

        if not keep:
            self.bits_buffer >>= n
            self.available_bits -= n

            return value
    
    
    def comp_codigo(self,tamanho):
        a=[]
        for i in range(tamanho):
            a.append(self.readBits(3))
        print(a)
        return self.code_order(a)
    
    
    def code_order(self,array):
        a=[]
        ordem=[3,17,15,13,11,9,7,5,4,6,8,10,12,14,16,18,0,1,2]
        for i in ordem:
            try:
                a.append(array[i])
            except IndexError:
                a.append(0)
        print(a)
        return a


    def Huff_code(self,array):
        contagem = [array.count(x) for x in range(max(array))]
        code = 0
        contagem[0] = 0
        next_code = []
        max_bits = max(array)+1
        for bits in range(1,max_bits):
            code = (code + contagem[bits-1]) << 1
            next_code.append(code)
        tree_code = []
        for n in array:
            if n != 0:
                tree_code.append(format(next_code[n-1],'b').zfill(n))
                next_code[n-1]+=1
            else: tree_code.append(0)
        print (tree_code)
        return tree_code
    
    
    def Huff_tree(self,array):
        huff_tree = HuffmanTree()
        simbolos = []
        for i in range(len(array)):
            simbolos.append(i)

        for i in range(len(array)):
            if array[i] !=0:
                huff_tree.addNode(array[i],simbolos[i])
        return huff_tree
    
    
    def comp(self,tree,limite):
        array=[]
        anterior=0
        while(len(array)<limite):
            bits=self.readBits(1)
            find_tree=tree.nextNode(str(bits))
            if(find_tree>=0):
                if(find_tree==16):
                    extra=self.readBits(2)+3
                    for i in range(extra):
                        array.append(anterior)
                    tree.resetCurNode()
                if(find_tree==17):
                    extra=self.readBits(3)+3
                    for i in range(extra):
                        array.append(0)
                    tree.resetCurNode()
                if(find_tree==18):
                    extra=self.readBits(7)+11
                    for i in range(extra):
                        array.append(0)
                    tree.resetCurNode()
                if(find_tree<16):
                    array.append(find_tree)
                    tree.resetCurNode()
                anterior=find_tree
        print(array)
        return array
    
    
    def decode_data(self,HLIT,HDIST):
        data=[]
        array=[]
        while(1):
            bits=self.readBits(1)
            find_tree=HLIT.nextNode(str(bits))
            if(find_tree>=0):
                if(find_tree<256):
                    data.append(find_tree)
                    HLIT.resetCurNode()
                if(find_tree==256):
                    break
                if(find_tree>256):
                    HLIT.resetCurNode()
                    lenght=self.extra_lenght(find_tree)
                    bits=self.readBits(1)
                    find_extra_tree=HDIST.nextNode(str(bits))
                    while(find_extra_tree<0):
                        bits=self.readBits(1)
                        find_extra_tree=HDIST.nextNode(str(bits))
                    HDIST.resetCurNode()
                    distance=self.extra_distance(find_extra_tree)
                    if(distance>=lenght):
                        for i in range(lenght):
                            array.append(data[-distance+i])
                        for j in array:
                            data.append(j)
                        array.clear()
                    else:
                        for i in range(distance):
                            array.append(data[-distance+i])
                        for j in range(lenght-distance):
                            array.append(data[-distance+j])
                        for k in array:
                            data.append(k)
                        array.clear()
        return data
                    
                
    def extra_lenght(self,num):
        lenght=0
        d={257:3,265:11,269:19,273:35,277:67,281:131,285:258}
        keys=[x for x in d.keys()]
        for x in range(1,len(keys)):
            if num < keys[x]:
                bits=self.readBits(x-1)
                lenght=d[keys[x-1]]+(num-keys[x-1])*2**(x-1)+bits
                break
            if num == 285:
                lenght=258
                break
        return lenght
        
            
    def extra_distance(self,num):
        distance=0
        d={0:1,4:5,6:9,8:17,10:33,12:65,14:129,16:257,18:513,20:1025,22:2049,24:4097,26:8193,28:16385}
        keys=[x for x in d.keys()]
        for x in range(1,len(keys)):
            if num < keys[x]:
                bits=self.readBits(x-1)
                distance=d[keys[x-1]]+(num-keys[x-1])*2**(x-1)+bits
                break
            if(num >= keys[-1]):
                y=len(keys)-1
                bits=self.readBits(y)
                distance=d[keys[y]]+(num-keys[y])*2**(y)+bits
                break
        return distance
        
    
    def load_file(self,array):
        name=self.gzh.fName
        file=open(name,'wb')
        for i in array:
            file.write(i.to_bytes(1,"big"))
        file.close()
            


if __name__ == '__main__':
	# gets filename from command line if provided
	fileName = "C:/Users/NB233/Downloads/TP2/public/base code - python/FAQ.txt.gz"
	if len(sys.argv) > 1:
		fileName = sys.argv[1]			

	# decompress file
	gz = GZIP(fileName)
	gz.decompress()
	