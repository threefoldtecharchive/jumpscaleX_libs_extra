@0xa16088fb1cfdaa20;

#unique id of an object is 6 bytes: region+uid




struct User {
  region @0; UInt16; #is identificaton of region, in beginning = 0
  id @1 :UInt32; #4 bytes, means max 4billion entries max
  epoch @2: UInt32; #moddate
  pubkey @2; Data; #32 bytes (use https://github.com/philanc/luatweetnacl)
  history @4: UInt32; #if there is a previous version of this user (e.g. if pubkey changes)
  sign @5 :Data; #48 bytes: has been signed by secret key of User & returns the 16 byte blake hash
                        # of previousobj:sign + current:region+rid+epoch+pubkey+history+link
  link @6 :UInt32; #link to Base object which has all data for this user in namespace 1 which is special namespace for user

}
#size: 2+4+4+32+4+48 = 94 bytes
#2 billion entries = 175 GB


struct Base {
  region @0; UInt16;    #is identificaton of region, in beginning = 0
  id @1 :UInt32;       #4 bytes, means max 4billion entries max
  epoch @2: UInt32;     #moddate
  author @3: UInt32;    #has to be admin or the original author
  history @4: UInt32;   #if there is a previous version of this item
  data  @5 :Data;       #the payload, if a new version is made with empty data, this means this object has been deleted
  crc  @6: UInt32;
  namespace @7: UInt32;
  admins @8 :List(UInt32);  #list of authors who can modify, only if author is member of admins list the it can create a new version of this obj
                            #if  admins==[] then only the original author can modify or create new versions

  sign @9 :Data;        #48 bytes: has been signed by secret key of User & returns the 16 byte blake hash
                            # of previousobj:sign + current:region+rid+epoch+author+history+data+crc+namespace+admins
}
#overhead: 2+4+4+4+4+4+4+48+?=74+? bytes

########### ALL BELOW ARE EMBEDDED IN DATA PROPERTY OF BASE

#data for group (sits in the Base data property)
struct Group {
  link @6 :UInt32;          #link to GroupDetail object which has all data for this group in namespace 2 which is special namespace for group
  members @6: List(UInt32)  #all users which are part of this group
  admins @7: List(UInt32)   #all users which can administer this group, last author has to be part of admin & has to have signed
}


struct Region {
  region @0; UInt16; #is identificaton of region, in beginning = 0
  country @1; UInt16; #e.g. 32 = Belgium
}

struct Server {
  regions @0; List(UInt16); #is list of regions this server operate for
  addr @1; Data; #ipaddr how to be reached
  guardians @2: List(UInt32)   #these are groups who can ask server to halt operation (add Server record with data = "" linking to previous)
  byte1 @3:Data

}

struct Server {
  regions @0; List(UInt16); #is list of regions this server operate for
  addr @1; Data; #ipaddr how to be reached

}



struct Base {

  uid @0 :UInt32; #4 bytes, means max 4billion entries per namespace
  nsid @1: UInt32: #4 bytes for the namespace id

  author @2 :UInt32; #4 bytes
  sign @3 :UInt64; #8 bytes signing as done by author (for whatever is put in data)

  data @4: Data; #the payload of the data

  crc  @5 : UInt32; #crc of the data (can verify the data without having to use the pub key of the author)

  epoch @6: UInt32; #moddate



  previous @8: UInt32; #if there is a previous version of this item

  index1 @4 : Int32; #index 1 which is an int 32
  index2 @5 : Int64; #index 2 which is an int 64
  index3 @6 : Text; #index 3 which is always text
  index4 @7 : Text; #index 3 which is always text
  index4 @8 : Text; #index 3 which is always text
  index4 @9 : Text; #index 3 which is always text


}

struct ACL {

  uid @0 :Int32; #4 bytes, means max 4billion entries per namespace
  nsid @1: Int32: #4 bytes for the namespace id
