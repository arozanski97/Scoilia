#!/usr/bin/env python3

import os
import subprocess
import argparse
from webserver.backend import db_util

######################################################################## Make directories #############################################################################
def makeDir(output_directory):

    subprocess.run("mkdir "+str(output_directory), shell=True)

    subprocess.run("mkdir tool_output", shell=True)
    subprocess.run("mkdir temp", shell=True)

    subprocess.run("mkdir tool_output/org_cds_db", shell=True)
    subprocess.run("mkdir tool_output/MergedBLAST", shell=True)

    subprocess.run("mkdir tool_output/prodigal_fasta_result", shell=True)
    subprocess.run("mkdir tool_output/prodigal_gff_result", shell=True)
    subprocess.run("mkdir tool_output/gms2_fasta_result", shell=True)
    subprocess.run("mkdir tool_output/gms2_gff_result", shell=True)

    subprocess.run("mkdir tool_output/prodigal_gms2_intersection", shell=True)
    subprocess.run("mkdir tool_output/prodigal_bedtools", shell=True)
    subprocess.run("mkdir tool_output/gms2_bedtools", shell=True)

    subprocess.run("mkdir tool_output/MergedGFF", shell=True)
    subprocess.run("mkdir "+output_directory+"/MergedFASTA", shell=True)

############################################################ Creating database of organism CDS for BLAST ##############################################################
def blastDatabase(org_cds):

    command = "makeblastdb -in "+str(org_cds)+" -dbtype nucl -out tool_output/org_cds_db/blast"
    subprocess.call(command.split())

######################################################################### Run Prodigal ################################################################################
def runProdigal(input_file):

    command = "prodigal -i "+str(input_file)+" -d tool_output/prodigal_fasta_result/prodigal_fasta_"+str(input_file.split("/")[-1])+" -f gff -o tool_output/prodigal_gff_result/prodigal_gff_"+str(input_file.split("/")[-1].replace(".fasta",""))
    subprocess.call(command.split())

    #subprocess.call("rm tool_output/prodigal_gff_result/*.fai", shell=True)
    #subprocess.call("rm tool_output/prodigal_fasta_result/*.fai", shell=True)
    subprocess.call("rm tool_output/prodigal_gff_result/*.DS_Store", shell=True)
    subprocess.call("rm tool_output/prodigal_fasta_result/*.DS_Store", shell=True)

####################################################################### Run GeneMarkS-2 ###############################################################################
def runGMS2(input_file):

    command = "perl ../Python_Scripts/gms2_linux_64/gms2.pl --seq "+str(input_file)+" --genome-type auto --fnn tool_output/gms2_fasta_result/gms2_fasta_"+str(input_file.split("/")[-1])+" --output tool_output/gms2_gff_result/gms2_gff_"+str(input_file.split("/")[-1].replace(".fasta",""))+" --format gff"
    subprocess.call(command.split())

    #Move and remove temporary files generated by GMS2 to temp directory:
    subprocess.run("mv GMS2.mod temp", shell=True)
    subprocess.run("mv log temp", shell=True)
    subprocess.run("rm -rf temp", shell=True)

################################################################### Run BEDTools intersection #########################################################################
def runBedtoolsIntersect(input_file, output_directory):

    prodigal_file = sorted(os.listdir("tool_output/prodigal_gff_result/"))
    print(prodigal_file)

    gms2_file = sorted(os.listdir("tool_output/gms2_gff_result/"))
    #gsm2_file = gms2_file.sort()
    print(gms2_file)

    for i,j in zip(gms2_file,prodigal_file):
        #Running bedtools intersect to obtain the intersection of GMS2 and Prodigal:
        subprocess.run("bedtools intersect -f 1,0 -r -a tool_output/gms2_gff_result/"+i+" -b tool_output/prodigal_gff_result/"+j+" > tool_output/prodigal_gms2_intersection/"+i+"_"+j, shell=True)
        #subprocess.run("rm tool_output/prodigal_gms2_intersection/*.fai",shell=True)

        #Running bedtools intersect to obtain only GMS2:
        subprocess.run("bedtools intersect -f 1,0 -r -v -a tool_output/gms2_gff_result/"+i+" -b tool_output/prodigal_gff_result/"+j+" > tool_output/gms2_bedtools/"+i+"_"+j, shell=True)
        #subprocess.run("rm tool_output/gms2_bedtools/*.fai",shell=True)

        #Running bedtools intersect to obtain only Prodigal:
        subprocess.run("bedtools intersect -f 1,0 -r -v -a tool_output/prodigal_gff_result/"+j+" -b tool_output/gms2_gff_result/"+i+" > tool_output/prodigal_bedtools/"+i+"_"+j, shell=True)
        #subprocess.run("rm tool_output/prodigal_bedtools/*.fai",shell=True)

    files1 = os.listdir("tool_output/prodigal_gms2_intersection/")
    files2 = os.listdir("tool_output/gms2_bedtools/")
    files3 = os.listdir("tool_output/prodigal_bedtools/")

    #Concatenating the above three results to obtain a merged GFF file:
    for i,j,k in zip(files1,files2,files3):
        subprocess.run("cat tool_output/prodigal_gms2_intersection/"+i+" tool_output/gms2_bedtools/"+j+" tool_output/prodigal_bedtools/"+k+" > tool_output/MergedGFF/final_merged_gff_"+i+j+k, shell=True)
        #subprocess.run("tool_output/MergedGFF/*.fai", shell=True)

######################################################################### Get FASTA files #############################################################################
def runGetFASTA(input_file, output_directory):

    files4 = sorted(os.listdir("tool_output/MergedGFF/"))
    files5 = os.listdir(input_file)

    #Running bedtools getfasta to obtain FASTA files:
    for i,j in zip(files5,files4):
        subprocess.run("bedtools getfasta -fi "+input_file+"/"+i+" -bed tool_output/MergedGFF/"+j+" > "+output_directory+"/MergedFASTA/merged_fasta_"+i, shell=True)
        subprocess.run("rm "+input_file+"/"+"*.fai", shell=True)

        subprocess.run("rm "+output_directory+"/MergedFASTA/"+"*.DS_Store", shell=True)

########################################################################## Run BLASTN ##################################################################################
def runBLAST(output_directory):
    files6 = sorted(os.listdir(output_directory+"/MergedFASTA/"))
    print(files6)

    for i in files6:

        #Running BLASTN and saving results in tab-spaced column (Output format 6):
        subprocess.run("blastn -db tool_output/org_cds_db/blast -query "+output_directory+"/MergedFASTA/"+i+ " -outfmt 6 -max_hsps 1 -max_target_seqs 1 -num_threads 8 > tool_output/MergedBLAST/"+i.replace("merged_fasta","blast_outfmt")+".out", shell=True)

        subprocess.run("rm tool_output/MergedBLAST/*.DS_Store.out", shell=True)

########################################################### True Positive (TP) / False Positive (FP) #######################################################################
def runRename(FASTA_files, BLAST_files):

    with open(FASTA_files, "r") as fh:
        fasta_file = fh.readlines()

    with open(BLAST_files, "r") as fh:
        blast_file = fh.readlines()
    blast_header = []

    for line in blast_file:
        blast_header.append(line.split("\t")[0])

    write_output = open(FASTA_files, "w")

    for line in fasta_file:
        if line.startswith(">"):
            fasta_header = line.split(">")[1]
            fasta_header = fasta_header.rstrip("\n")

            if fasta_header in blast_header:                                    #If FASTA header matches the BLAST header (if there is a hit), then: True Positive (TP)
                line = line.rstrip("\n")
                write_output.write(line + " TP"+"\n")
            else:                                                               #Else FASTA header does NOT match the BLAST header (if there is no hit), then: False Positive (FP)
                line = line.rstrip("\n")
                write_output.write(line + " FP"+"\n")
        else:                                                                   #Writes the sequence of the respective FASTA header
            write_output.write(line)
    write_output.close()

######################################################################## main function ####################################################################################

def f(input_path, org_cds, output_path, flag):
#def main():
    '''
    #Argparse code:
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", help = "Complete path of input directory containing FASTA files to be analyzed.")
    parser.add_argument("-b", help = "Organism of interest's CDS FASTA file.")
    parser.add_argument("-o", help = "Output directory name for your outputs.")
    args = parser.parse_args()

    #Populating variables:
    input_path = args.i
    org_cds = args.b
    output_path = args.o
    '''

    #Calling functions:
    makeDir(output_path)
    blastDatabase(org_cds)
    filename1 = os.listdir(input_path)
    for files in filename1:
        runProdigal(input_path+"/"+files)
        runGMS2(input_path+"/"+files)
    runBedtoolsIntersect(input_path, output_path)
    runGetFASTA(input_path, output_path)
    runBLAST(output_path)
    filename2 = sorted(os.listdir(output_path+"/MergedFASTA/"))
    filename3 = sorted(os.listdir("tool_output/MergedBLAST/"))
    for i,j in zip(filename2,filename3):
        runRename(output_path+"/MergedFASTA/"+i,"tool_output/MergedBLAST/"+j)

    if flag == 0:
        db_util.update_pipeline_status(input_path.split('/')[-2])
    print(output_path)
    p=subprocess.Popen(["tar","-czvf",output_path+".tar.gz",output_path], stdout=subprocess.PIPE)
    out=p.communicate()
    print (input_path)
    input_path=input_path.split('/')[0:4]
    input_path='/'.join(input_path)
    print (input_path)
    p=subprocess.Popen(["rm","-r",input_path], stdout=subprocess.PIPE)
    out=p.communicate()

#if __name__ == "__main__":
    #main()
