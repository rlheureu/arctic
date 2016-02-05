#
# Script to load data
#
#
LOAD DATA LOCAL INFILE '/Users/shanrandhawa/Downloads/arctic_component.csv' INTO TABLE arctic.arctic_component FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 rows
(arctic_component_id,
vendor_name,
brand_name,
model_number,
max_performance,
data_type_discriminator,
generation,
int_gpu,
socket,
ddr3,
ddr3l,
ddr4,
max_memory_size,
@unlocked,
@dx12_cap,
@display_port,
@hdmi,
@dvi,
@vga) set
unlocked=IF(@unlocked = '', NULL, cast(@unlocked as signed)),
dx12_cap=IF(@dx12_cap = '', NULL, cast(@dx12_cap as signed)),
display_port=IF(@display_port = '', NULL, cast(@display_port as signed)),
hdmi=IF(@hdmi = '', NULL, cast(@hdmi as signed)),
dvi=IF(@dvi = '', NULL, cast(@dvi as signed)),
vga=IF(@vga = '', NULL, cast(@vga as signed));