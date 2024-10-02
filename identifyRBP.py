# Paths for the CLIP-seq databases
#human_clip_path = '/Users/student/Desktop/RNADATA_RBP/Target.bed'
#mouse_clip_path = '/Users/student/Desktop/RNADATA_RBP/Target.bed'

import streamlit as st
import subprocess
import os

# Function to run shell commands
def run_command(command):
    """Run a shell command and return output."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip()

# Set up the Streamlit app
st.title('RBPFinder')
st.subheader('Analysis of potential RBP interactions with genomic targets')

# Paths for the CLIP-seq databases
human_clip_path = '/Users/student/Desktop/RNADATA_RBP/Target.bed'
mouse_clip_path = '/Users/student/Desktop/RBP.Analysis/mm10togh38.bed'

# Paths for genome files
genome_file_human = '/Users/student/Desktop/RNADATA_RBP/hg38.chrom.sizes'
genome_file_mouse = '/Users/student/Desktop/RNADATA_RBP/mm10.chrom.sizes'

# Path for mouse to human BED file
mouse_to_human_bed = '/Users/student/Desktop/RBP.Analysis/RefClipDataBAse.bed'

# Step 1: Access CLIP-seq Database
st.header('Step 1: Access CLIP-seq Database')

# Load and display Human CLIP-seq Database
st.subheader('Human CLIP-seq Database')
if os.path.exists(human_clip_path):
    with open(human_clip_path, 'r') as f:
        human_clip_data = f.read()
    st.text_area("Human CLIP-seq Data (eCLIP, HITS-CLIP, PAR-CLIP):", human_clip_data, height=200)
else:
    st.error("Human CLIP-seq database file not found.")

# Load and display Mouse CLIP-seq Database
st.subheader('Mouse CLIP-seq Database')
if os.path.exists(mouse_clip_path):
    with open(mouse_clip_path, 'r') as f:
        mouse_clip_data = f.read()
    st.text_area("Mouse CLIP-seq Data (eCLIP, HITS-CLIP, PAR-CLIP):", mouse_clip_data, height=200)
else:
    st.error("Mouse CLIP-seq database file not found.")

# Step 2: Upload Target BED File
st.header('Step 2: Upload Your Target BED File')
uploaded_file = st.file_uploader("Choose a BED file", type="bed")

# Step 3: Convert BED Files to Consistent Genome Versions
if uploaded_file is not None:
    # Save uploaded BED file temporarily
    target_bed_path = 'target_exons.bed'
    with open(target_bed_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    
    st.success("Uploaded target BED file.")

    # Step 4: Expand Coordinates of Target Exons by User-Defined Bases
    st.header('Step 3: Expand Target Exons')

    # Dropdown menu for user to select number of base pairs
    bp_options = [50, 100, 150, 200, 250]
    selected_bp = st.selectbox("Select number of base pairs to expand:", bp_options)

    # Dropdown menu for user to select organism
    organism = st.selectbox("Select Organism:", ["Select", "Human", "Mouse"])

    if st.button("Expand Target Exons"):
        if organism == "Select":
            st.error("Please select an organism before proceeding.")
        else:
            # Determine genome file based on selected organism
            if organism == "Human":
                genome_file = genome_file_human
            else:
                genome_file = genome_file_mouse

            if os.path.exists(genome_file):
                command_slop = f"bedtools slop -i {target_bed_path} -g {genome_file} -b {selected_bp} > extended_exons.bed"
                st.code(command_slop)  # Display the command being run
                stdout, stderr = run_command(command_slop)
                if stderr:
                    st.error(f"Error during expansion: {stderr}")
                else:
                    st.success(f"Target exons expanded by {selected_bp} bases successfully to `extended_exons.bed`.")

                    # Allow the user to download the extended exons file
                    with open('extended_exons.bed', 'r') as f:
                        extended_exons_data = f.read()
                    st.download_button(
                        label="Download Extended Exons",
                        data=extended_exons_data,
                        file_name='extended_exons.bed',
                        mime='text/plain'
                    )
            else:
                st.error("Genome file does not exist. Please check the file name.")

    # Step 5: Intersect with CLIP-seq Data
    st.header('Step 4: Intersect Extended Targets with CLIP-seq Data')

    if os.path.exists('extended_exons.bed'):
        st.write("Using `extended_exons.bed` for intersection.")

        # Use the predefined mouse to human BED file for the mouse organism
        if organism == "Mouse":
            st.write(f"Using the predefined mouse-to-human BED file: {mouse_to_human_bed}")
            clip_bed_path = mouse_to_human_bed  # Use the predefined file directly
        elif organism == "Human":
            # Upload CLIP-seq Data for Human
            uploaded_clip_file = st.file_uploader("Upload Human CLIP-seq BED file", type="bed", key='clipfile')

            if uploaded_clip_file is not None:
                clip_bed_path = 'CLIP_peaks.bed'
                with open(clip_bed_path, 'wb') as f:
                    f.write(uploaded_clip_file.getbuffer())
                st.success("Uploaded CLIP-seq BED file.")
            else:
                st.warning("Please upload the Human CLIP-seq BED file.")

        if organism in ["Mouse", "Human"] and st.button("Intersect with CLIP-seq Data"):
            # Show the command being executed
            if organism == "Mouse":
                command_intersect = f"bedtools intersect -a extended_exons.bed -b {clip_bed_path} -wb| sort -u > unique_overlaps.bed"
            else:
                command_intersect = f"bedtools intersect -a extended_exons.bed -b {clip_bed_path} | sort -u > unique_overlaps.bed"

            st.code(command_intersect)  # Display the command being run

            stdout, stderr = run_command(command_intersect)
            if stderr:
                st.error(f"Error during intersection: {stderr}")
            else:
                st.success("Intersection completed. Unique overlaps saved to `unique_overlaps.bed`.")

                # Allow the user to download the unique overlaps file
                with open('unique_overlaps.bed', 'r') as f:
                    unique_overlaps_data = f.read()
                    
                # Check if the file is empty
                if not unique_overlaps_data.strip():
                    st.error("The resulting unique overlaps file is empty.")
                else:
                    st.download_button(
                        label="Download Unique Overlaps",
                        data=unique_overlaps_data,
                        file_name='unique_overlaps.bed',
                        mime='text/plain'
                    )

                    # Display the contents of unique_overlaps.bed
                    st.subheader("Contents of Unique Overlaps:")
                    st.text_area("Unique Overlaps Data:", unique_overlaps_data, height=200)

                    # Count lines in unique_overlaps.bed
                    line_count_command = "wc -l unique_overlaps.bed"
                    st.code(line_count_command)  # Display the line count command
                    line_count, line_count_err = run_command(line_count_command)
                    if line_count_err:
                        st.error(f"Error counting lines: {line_count_err}")
                    else:
                        st.write(f"Number of unique overlaps: {line_count}")
    else:
        st.error("`extended_exons.bed` not found. Please run Step 3 first.")

# Step 6: Extract RBP Information
st.header('Step 5: Extract RBP Information')

# Input field for the column name to cut from unique_overlaps.bed
column_name = st.text_input("Enter the column name to extract RBP data from `unique_overlaps.bed` (e.g., 1 for first column):")

if st.button("Extract RBP Information"):
    if os.path.exists('unique_overlaps.bed'):
        if column_name.isdigit():  # Check if the input is a digit
            command_rbp = f"cut -f {column_name} unique_overlaps.bed | sort | uniq -c | sort -nr | awk '{{print $2 \"\\t\" $1}}' > rbp_table.txt"
            st.code(command_rbp)  # Display the command being run
            stdout_rbp, stderr_rbp = run_command(command_rbp)
            if stderr_rbp:
                st.error(f"Error during RBP extraction: {stderr_rbp}")
            else:
                st.success("RBP information extracted successfully to `rbp_table.txt`.")

                # Allow the user to download the RBP table file
                with open('rbp_table.txt', 'r') as f:
                    rbp_table_data = f.read()
                st.download_button(
                    label="Download RBP Table",
                    data=rbp_table_data,
                    file_name='rbp_table.txt',
                    mime='text/plain'
                )

                # Display the contents of rbp_table.txt
                st.subheader("Contents of RBP Table:")
                st.text_area("RBP Table Data:", rbp_table_data, height=200)
        else:
            st.error("Please enter a valid column number.")
    else:
        st.error("`unique_overlaps.bed` not found. Please run Step 4 first.")

# Footer
st.write("### Note:")
st.write("Ensure you have Bedtools installed in your environment for this tool to function correctly.")
