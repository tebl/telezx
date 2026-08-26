const BASE_URL = "https://raw.githubusercontent.com/tebl/telezx-content/main/out/";

const ASCII_SPACE = 32;
const ATTRIBUTE = {
    BLACK:   0b00000000,
    BLUE:    0b00000001,
    RED:     0b00000010,
    MAGENTA: 0b00000011,
    GREEN:   0b00000100,
    CYAN:    0b00000101,
    YELLOW:  0b00000110,
    WHITE:   0b00000111,
    FLASH:   0b10000000,
    BRIGHT:  0b01000000
};
const ERROR_ATTRIBUTE = zx_to_attribute(false, false, ATTRIBUTE.RED, ATTRIBUTE.WHITE);
const ERROR_DESCRIPTION = zx_to_attribute(false, true, ATTRIBUTE.BLACK, ATTRIBUTE.RED);
const STYLE_DEFAULT = zx_to_attribute(false, false, ATTRIBUTE.BLACK, ATTRIBUTE.WHITE);
const STYLE_HEADER = zx_to_attribute(false, true, ATTRIBUTE.BLACK, ATTRIBUTE.WHITE);
const STYLE_HEADER_INPUT = zx_to_attribute(false, false, ATTRIBUTE.BLACK, ATTRIBUTE.GREEN);
const STYLE_HEADER_FIELD = zx_to_attribute(false, false, ATTRIBUTE.BLACK, ATTRIBUTE.YELLOW);
const STYLE_LINK_A = zx_to_attribute(false, false, ATTRIBUTE.BLUE, ATTRIBUTE.WHITE);
const STYLE_LINK_B = zx_to_attribute(false, false, ATTRIBUTE.RED, ATTRIBUTE.WHITE);
const STYLE_LINK_C = zx_to_attribute(false, false, ATTRIBUTE.MAGENTA, ATTRIBUTE.WHITE);
const DOCUMENT_ZERO = 0;

const RGB_BASE = 0xe0;
const RGB_FULL = 0xff;

const DOCUMENT_DEFAULT = 1000;
const PAGE_MINIMUM = 1;
const PAGE_MAXIMUM = 9999;
const SCREEN_REFRESH = 1000/50;
const SCREEN_WIDTH_CHARS = 32;
const SCREEN_HEIGHT_CHARS = 24;
const SIZE_DATA = 6144;
const SIZE_ATTR = 768;
const SIZE_MEMORY = SIZE_DATA + SIZE_ATTR;

const STATUS_TYPES = { NONE: -1, OK: 0, ERROR: 1 };
const INDEX_TYPES = { NONE: 'NONE', INDEX: 'IDX' };
const ASSET_TYPES = { TOKEN: 0xaa, SCR: 0x55}
const SPECSCII_TOKEN = {
    ENTER: 0x0d,
    INK: 0x10,
    PAPER: 0x11,
    FLASH: 0x12,
    BRIGHT: 0x13,
    INVERT: 0x14,
    CURSOR: 0x16
};

const buffer = new ArrayBuffer(SIZE_MEMORY);
const memory = new Uint8Array(buffer);
const screen_map = zx_calculate_lookup_table();

var cursor_x = 0;
var cursor_y = 0;

var current_font = FONT_DEFAULT;
var current_document = DOCUMENT_DEFAULT;
var current_page = -1;
var current_input = ""

var current_index = null;
var current_status = "";
var current_status_type = STATUS_TYPES.NONE;

// Get the canvas and context
var canvas;
var context;
var canvas_width;
var canvas_height;
var canvas_image;
var canvas_interval_id;
var canvas_flash_timer = 0;
var canvas_flash_value = false;

function zx_calculate_lookup_table() {
    var lookup = Array();
    for (var pos_x = 0; pos_x < SCREEN_WIDTH_CHARS; pos_x++) {
        lookup[pos_x] = Array();
        for (var pos_y = 0; pos_y < SCREEN_HEIGHT_CHARS; pos_y++) {
            var lot = Math.trunc(pos_y / 8);
            var address = (lot*0x800) + (pos_y - lot*8)*SCREEN_WIDTH_CHARS + pos_x;
            lookup[pos_x][pos_y] = address;
        }
    }
    return lookup;
}

function ui_incrementCursor() {
    cursor_x++;
    if (cursor_x >= SCREEN_WIDTH_CHARS) {
        cursor_x = 0;
        cursor_y++;
        if (cursor_y >= SCREEN_HEIGHT_CHARS) {
            cursor_y = 0;
        }
    }
}

function ui_set_cursor(pos_x, pos_y) {
    cursor_x = pos_x % SCREEN_WIDTH_CHARS;
    cursor_y = pos_y % SCREEN_HEIGHT_CHARS;
}

function zx_clear_attributes(new_value) {
    for (var address = SIZE_DATA; address < SIZE_MEMORY; address++) {
        memory[address] = new_value;
    } 
}

function zx_clear_memory(new_data_value, new_attribute_value) {
    for (var address = 0; address < SIZE_MEMORY; address++) {
        memory[address] = (address < SIZE_DATA) ? new_data_value : new_attribute_value;
    } 
}

function ui_print_bytes(data) {
    zx_set_pixels_at(cursor_x, cursor_y, data)
    ui_incrementCursor();
}

function ui_print_ascii(character) {
    ui_print_bytes(ui_get_font_data(character - ASCII_SPACE));
}

function ui_set_ascii_at(cursor_x, cursor_y, character) {
    zx_set_pixels_at(
        cursor_x, 
        cursor_y, 
        ui_get_font_data(character - ASCII_SPACE)
    );
}

function ui_get_font_data(character) {
    var offset = character*8;
    if (character < 0 || character >= 96) offset = 0;
    return current_font.slice(offset, offset + 8);
}

function ui_print_glyph(character) {
    ui_print_bytes(ui_get_glyph_data(character - 0x80));
}

function ui_get_glyph_data(character) {
    var offset = character*8;
    if (character < 0 || character >= 16) offset = 0;
    return FONT_GLYPHS.slice(offset, offset + 8);
}

function ui_printString(string, attribute) {
    for (var i = 0; i < string.length; i++) {
        if (attribute >= 0) ui_set_cursor_attribute(attribute);
        ui_print_ascii(string.charCodeAt(i));
    }
}

function zx_set_attribute_at(pos_x, pos_y, value) {
    var index = (pos_y * SCREEN_WIDTH_CHARS) + pos_x;
    memory[SIZE_DATA + index] = value;
}

function zx_set_pixels_at(pos_x, pos_y, values) {
    var address = screen_map[pos_x][pos_y];
    for (var i = 0; i < 8 && i < values.length; i++) {
        memory[address + i*0x100] = values[i];
    }
}

function ui_set_cursor_attribute(value) {
    zx_set_attribute_at(cursor_x, cursor_y, value);
}

function ui_set_cursor_data(values) {
    zx_set_pixels_at(cursor_x, cursor_y, values);
}

function ui_set_font(font) {
    current_font = font;
}

function zx_to_attribute(is_flashing, is_bright, paper, ink) {
    return ((is_flashing ? ATTRIBUTE.FLASH : 0x00) | (is_bright ? ATTRIBUTE.BRIGHT : 0x00) | (paper << 3) | ink);
}

function zx_swap_attribute(attribute) {
    parsed = zx_parse_attribute(attribute);
    return zx_to_attribute(
        parsed.flash, 
        parsed.bright,
        parsed.ink,
        parsed.paper
    );
}

function zx_parse_attribute(attribute) {
    return {
        flash: (attribute & ATTRIBUTE.FLASH) == ATTRIBUTE.FLASH,
        bright: (attribute & ATTRIBUTE.BRIGHT) == ATTRIBUTE.BRIGHT,
        paper: (attribute & 0b00111000) >>> 3,
        ink: attribute & 0b00000111
    }
}

function ui_clear_canvas(red, green, blue, alpha) {
    for (var x = 0; x < canvas_width; x++) {
        for (var y = 0; y < canvas_height; y++) {
            // Get the pixel index
            var pixelindex = (y * canvas_width + x) * 4;
            ui_set_canvas_index(pixelindex, red, green, blue, alpha);
        }
    }
}

function ui_set_canvas_index(index, red, green, blue, alpha) {
    canvas_image.data[index] = red;
    canvas_image.data[index + 1] = green;
    canvas_image.data[index + 2] = blue;
    canvas_image.data[index + 3] = alpha;
}

function ui_set_canvas_pixel(x, y, red, green, blue, alpha) {
    ui_set_canvas_index((y * canvas_width + x) * 4, red, green, blue, alpha);
}

function get_canvas_colour(is_on, attr_value) {
    var colour = (is_on ? attr_value.ink : attr_value.paper);
    if (attr_value.flash && canvas_flash_value) {
        colour = (is_on ? attr_value.paper : attr_value.ink);
    }
    var base_value = (attr_value.bright ? RGB_FULL : RGB_BASE);
    return [
        ((colour >> 1) & 1)*base_value,  // red
        ((colour >> 2) & 1)*base_value,  // green
        (colour & 1)*base_value          // blue
    ];
}

function check_bit(number, bit) {
    var bit_mask = (1 << (7 - bit));
    return (number & bit_mask) != 0;
}

function render_memory() {
    for (var lot = 0; lot < 3; lot++) {
        for (var line = 0; line < 8; line++) {
            for (var row = 0; row < 8; row++) {
                for (var col = 0; col < SCREEN_WIDTH_CHARS; col++) {
                    var data_idx = lot * 2048 + (line * 8 + row) * SCREEN_WIDTH_CHARS + col;
                    var data_value = memory[data_idx];

                    var attr_idx = lot * 256 + row * SCREEN_WIDTH_CHARS + col;
                    var attr_value = zx_parse_attribute(memory[SIZE_DATA + attr_idx]);

                    for (var bit = 0; bit < 8; bit++) {
                        var x = col * 8 + bit;
                        var y = lot * 64 + row * 8 + line;

                        [red, green, blue] = get_canvas_colour(check_bit(data_value, bit), attr_value);
                        ui_set_canvas_pixel(x, y, red, green, blue, 255);
                    }
                }
            }
        }
    }
}

function get_date_string() {
    var d = new Date();
    return (
        String(d.getDate()).padStart(2, " ") + "." +
        String(d.getMonth() + 1).padStart(2, "0") + " " +
        String(d.getHours()).padStart(2, "0") + ":" +
        String(d.getMinutes()).padStart(2, "0") + ":" +
        String(d.getSeconds()).padStart(2, "0")
    )
}


function set_status(description, status_type) {
    current_status = description;
    current_status_type = status_type;
}

function set_error(description, clear_index=true) {
    set_status(description, STATUS_TYPES.ERROR);
    if (clear_index) {
        current_index = null;
    }
}

function have_error() {
    return current_status_type == STATUS_TYPES.ERROR;
}

function have_link(link_key) {
    if (current_index == null) return false;
    return (current_index[link_key] > DOCUMENT_ZERO);
}

function have_multiple_pages() {
    if (current_index == null) return false;
    return current_index.page_count > 1;
}

function have_page_id(page_id) {
    if (current_index == null) return false;
    if (current_index.page_count == 0) return false;
    return (page_id >= 0 && page_id < current_index.page_count);
}

function ui_overlay_headers() {
    ui_primary_header();
    if (ui_secondary_header_needed()) {
        ui_secondary_header();
    }
}

function ui_primary_header() {
    ui_set_font(FONT_DEFAULT);
    for (var i = 0; i < SCREEN_WIDTH_CHARS; i++) {
        zx_set_attribute_at(i, 0, STYLE_HEADER);
    }
    ui_set_cursor(0, 0);
    ui_printString("P", -1);
    ui_print_ascii(ASCII_SPACE);
    if (current_input == '') {
        ui_printString(String(current_document).padStart(4), -1);
    } else {
        ui_printString(current_input.padEnd(4, '-'), (current_input == '' ? -1 : STYLE_HEADER_INPUT));
    }
    ui_print_ascii(ASCII_SPACE);
    ui_print_ascii(ASCII_SPACE);
    ui_print_ascii(ASCII_SPACE);
    ui_set_font(FONT_CP850);
    ui_printString("T", zx_to_attribute(false, true, ATTRIBUTE.BLACK, ATTRIBUTE.RED));
    ui_printString("e", zx_to_attribute(false, true, ATTRIBUTE.BLACK, ATTRIBUTE.YELLOW));
    ui_printString("l", zx_to_attribute(false, true, ATTRIBUTE.BLACK, ATTRIBUTE.GREEN));
    ui_printString("e", zx_to_attribute(false, true, ATTRIBUTE.BLACK, ATTRIBUTE.BLUE));
    ui_printString("ZX", -1);
    ui_set_font(FONT_DEFAULT);
    ui_print_ascii(ASCII_SPACE);
    ui_print_ascii(ASCII_SPACE);
    ui_print_ascii(ASCII_SPACE);
    ui_printString(get_date_string(), STYLE_HEADER_FIELD);
    ui_set_font(FONT_DEFAULT);
}

function ui_secondary_header() {
    ui_set_font(FONT_DEFAULT);
    for (var i = 0; i < SCREEN_WIDTH_CHARS; i++) {
        zx_set_attribute_at(i, 23, STYLE_HEADER);
        ui_set_ascii_at(i, 23, ASCII_SPACE);
    }

    if (have_error()) {
        var max_chars = have_multiple_pages() ? (SCREEN_WIDTH_CHARS - 6) : SCREEN_WIDTH_CHARS;
        for (var i = 0; i < (max_chars); i++) {
            if (i < current_status.length) {
                zx_set_attribute_at(i, 23, ERROR_DESCRIPTION);
                ui_set_ascii_at(i, 23, current_status.charCodeAt(i));
            }
        }
    } else {
        ui_secondary_link('link_a', 'link_a_txt', 0, STYLE_LINK_A);
        ui_secondary_link('link_b', 'link_b_txt', 9, STYLE_LINK_B);
        ui_secondary_link('link_c', 'link_c_txt', 18, STYLE_LINK_C);
    }

    if (have_multiple_pages()) {
        ui_set_cursor(SCREEN_WIDTH_CHARS - 5, 23);
        ui_printString(
            String(current_page + 1).padStart(2, '0') + '/' + String(current_index.page_count).padStart(2, '0'),
            STYLE_HEADER_FIELD
        );
    }
}

function ui_secondary_link(link_key, link_key_desc, start_at, attribute) {
    if (current_index == null) return;
    if (have_link(link_key)) {
        var description = get_link_description(link_key, link_key_desc, 8);
        for (var i = 0; i < 8; i++) {
            zx_set_attribute_at((start_at + i), 23, attribute);
            if (i < description.length) {
                ui_set_ascii_at((start_at + i), 23, description.charCodeAt(i));
            } else {
                ui_set_ascii_at((start_at + i), 23, ASCII_SPACE);
            }
        }
    }
}

function get_link_description(link_key, link_key_desc, max_chars) {
    if (current_index[link_key_desc] == undefined || current_index[link_key_desc].length == 0) {
        return String(current_index[link_key]);
    }
    return get_centered_string(current_index[link_key_desc], max_chars);
}

function get_centered_string(value, max_chars) {
    if (value.length > max_chars) return value.slice(0, max_chars);
    return value.padStart(
        value.length + Math.trunc((max_chars - value.length) / 2)
    ).padEnd(max_chars);
}

function get_link_id(link_key) {
    if (current_index == null) return 0;
    return current_index[link_key];
}

function ui_secondary_header_needed() {
    if (have_error()) return true;
    if (have_multiple_pages()) return true;
    if (have_link('link_a')) return true;
    if (have_link('link_b')) return true;
    if (have_link('link_c')) return true;
    return false;
}

function render_screen(timestamp) {
    ui_overlay_headers();
    render_memory();

    // Draw the image data to the canvas
    context.putImageData(canvas_image, 0, 0);
}

/* We could call renderScreen directly, but that would lead to an inconsistent
 * framerate so instead we'll let the browser select a suitable time for us.
 */
function request_render_screen() {
    // renderScreen();
    window.requestAnimationFrame(render_screen);
}

/* Flashing is performed by ZX Spectrum ULA, and should be performed every 32
   frames according to some sites. It'll be prone to drifting though we don't
   really care about that.
*/
function schedule_periodic_refresh() {
    clearInterval(canvas_interval_id);
    canvas_interval_id = setInterval(
        periodic_refresh, 
        SCREEN_REFRESH
    );
}

/**
 * Perform a periodic refresh, scheduled using schedulePeriodicRefresh to
 * coincide with what should roughly be 50 fps. The flashing attributes
 * should toggle every 32 frames.
 */
function periodic_refresh() {
    canvas_flash_timer++;
    if (canvas_flash_timer > 31) {
        canvas_flash_timer = 0;
        canvas_flash_value = !canvas_flash_value;
    }
    request_render_screen();
}

/**
 * Called when we encounter a succesfully processed a page. Discards any
 * errors so that they don't hang around long enough to confuse anyone.
 */
function clear_status() {
    current_status = "";
    current_status_type = STATUS_TYPES.NONE;
}

/**
 * Get the base URL for a specific resource, note that everything will be
 * placed within a directory with the same name as the document ID.
 * Individual files will also start with the same name.
 * 
 * Example:
 *  https://raw.githubusercontent.com/tebl/telezx-content/main/out/<ID>/<ID>.<EXTENSION>
 *  https://raw.githubusercontent.com/tebl/telezx-content/main/out/<ID>/<ID>.<PAGE>.<EXTENSION>
 */
function get_base_url(page) {
    var padded_id = String(page).padStart(4, "0");
    var index_url = BASE_URL + padded_id + '/' + String(page).padStart(4, "0");
    return index_url;
}

function get_asset_url(page, subpage, extension) {
    var padded_id = String(subpage).padStart(2, "0");
    return get_base_url(page) + '.' + padded_id + extension;
}

function get_index_url() {
    return get_base_url(current_document) + ".idx";
}

function get_idx_hex(content, start, num_bytes) {
    return Number("0x" + content.slice(start, start + num_bytes));
}

function get_idx_page(content, start, num_bytes) {
    return Number(content.slice(start, start + num_bytes));
}

function get_idx_string(content, start, num_bytes) {
    return content.slice(start, start + num_bytes).replace(/\0.*$/g,'');
}

function get_scr_url(page, subpage) {
    return get_asset_url(page, subpage, ".scr");
}

function get_tkn_url(page, subpage) {
    return get_asset_url(page, subpage, ".tkn");
}

async function fetch_index() {
    try {
        // Fetch the JSON file  
        const response = await fetch(get_index_url());

        // Check for HTTP errors  
        if (!response.ok) {
            throw new Error(`${response.status} ${response.statusText}`);
        }

        // Parse JSON data  
        const content = await response.text();
        if (content.length >= 3) {
            parse_index(content);
        } else {
            set_error("Empty index");
        }
    } catch (error) {
        set_error(error.message);
        console.error("Failed to fetch data:", error);
    }

    request_render_screen();
}

function fetch_page() {
    var page = null;
    if (current_index == null) return generate_blank_page(ERROR_ATTRIBUTE);
    if (have_page_id(current_page)) page = current_index.pages[current_page];
    if (page == null) return generate_blank_page();
    
    if (page.type == ASSET_TYPES.TOKEN) {
        return fetch_token_asset(
            current_document, 
            current_page, 
            page.parameter);
    }
    if (page.type == ASSET_TYPES.SCR) {
        return fetch_scr_asset(
            current_document, 
            current_page);
    }

    return generate_blank_page(ERROR_ATTRIBUTE);
}

// function generatePage(page, subpage) {
//     zx_clear_memory(0x00, zx_toAttribute(false, false, ATTRIBUTES.BLACK, ATTRIBUTES.WHITE))

//     switch (subpage) {
//         case 0:
//             ui_setCursor(0, 2);
//             ui_setFont(FONT_DEFAULT);
//             ui_printString("Default:", zx_toAttribute(false, true, ATTRIBUTES.BLACK, ATTRIBUTES.YELLOW));
//             ui_setCursor(0, 3);
//             ui_setFont(FONT_DEFAULT);
//             for (let i = 0; i < (FONT_DEFAULT.length / 8); i++) {
//                 ui_printBytes(ui_getFontData(i));
//             }

//             ui_setCursor(0, 7);
//             ui_setFont(FONT_DEFAULT);
//             ui_printString("Computer:", zx_toAttribute(false, true, ATTRIBUTES.BLACK, ATTRIBUTES.YELLOW));
//             ui_setCursor(0, 8);
//             ui_setFont(FONT_CP850);
//             for (let i = 0; i < (FONT_DEFAULT.length / 8); i++) {
//                 ui_printBytes(ui_getFontData(i));
//             }
//             break;
//         case 1:
//         case 2:
//             let x = 1;
//             let y = 2;
//             let start = (subpage == 1 ? 0 : 0xc8);
//             let end = (subpage == 1 ? 0xc7 : 0xff);
//             for (let i = start; i <= end; i++) {
//                 ui_setCursor(x, y);
//                 ui_printString(i.toString(16).padStart(2, '0'), i);
//                 y++;
//                 if (y >= (SCREEN_HEIGHT_CHARS - 2)) {
//                     y = 2;
//                     x += 3;
//                 }
//             }
//             break;
//     }

//     setResponse(String(page), STATUS_TYPES.OK);
//     requestRenderScreen();
// }

function fetch_page_next() {
    if (have_page_id(current_page + 1)) {
        current_page += 1;
        fetch_page();
    }
}

function fetch_page_previous() {
    if (have_page_id(current_page - 1)) {
        current_page -= 1;
        fetch_page();
    }
}

async function fetch_scr_asset(page, subpage) {
    try {
        // Fetch the JSON file  
        const fetch_url = get_scr_url(page, subpage);
        const response = await fetch(fetch_url);

        // Check for HTTP errors  
        if (!response.ok) {
            throw new Error(`${response.status} ${response.statusText}`);
        }

        // Parse JSON data  
        const data = await response.bytes();
        if (data.length == memory.length) {
            for (var i = 0; i < memory.length; i++) {
                memory[i] = data[i];
            }
        } else {
            set_error("Not SCR");
            console.error("Data not consistent with SCR:", data.length);
        }

        clear_status();
    } catch (error) {
        console.error("Failed to fetch data:", error);
        set_error(error.message);
    }

    request_render_screen();
}

async function fetch_token_asset(page, subpage, default_attribute) {
    try {
        // Fetch the JSON file  
        const fetch_url = get_tkn_url(page, subpage);
        const response = await fetch(fetch_url);

        // Check for HTTP errors  
        if (!response.ok) {
            throw new Error(`${response.status} ${response.statusText}`);
        }

        // Parse JSON data  
        const data = await response.bytes();
        process_tokens(data, default_attribute);
    
        clear_status();
    } catch (error) {
        console.error("Failed to fetch data:", error);
        set_error(error.message, false);
        return;
    }

    request_render_screen();
}

function generate_blank_page(attribute) {
    if (typeof attribute == undefined) attribute = STYLE_DEFAULT;
    zx_clear_memory(0x00, attribute);
    request_render_screen();
    return true;
}

function process_tokens(data, default_attribute) {
    zx_clear_memory(0x00, default_attribute)

    ui_set_cursor(0, 0);
    let position = 0;
    let token_attribute = default_attribute;
    let mode_inverted = false;
    while (position < data.length) {
        // SPECSCII format constants
        // Stream format with embedded escape codes (ZX Spectrum BASIC control codes):
        // - 0x0D = Enter (CR+LF) - move to start of next line
        // - 0x10 XX = INK color (0-7)
        // - 0x11 XX = PAPER color (0-7)
        // - 0x12 XX = FLASH (0 or 1)
        // - 0x13 XX = BRIGHT (0 or 1)
        // - 0x14 XX = INVERSE (0 or 1) - swaps ink/paper
        // - 0x15 XX = OVER (0 or 1) - XOR mode
        // - 0x16 YY XX = AT row, col - position cursor
        // - 0x17 XX = TAB to column
        // - Other bytes = character codes (0x20-0x7F printable, 0x80-0xFF block graphics)

        const current_byte = data[position];
        switch (current_byte) {
            case SPECSCII_TOKEN.BRIGHT:
                position++;
                token_attribute = (token_attribute & 0xbf) | (data[position] << 6);
                position++;
                continue;
            
            case SPECSCII_TOKEN.CURSOR:
                position++;
                const set_y = data[position];
                position++;
                const set_x = data[position];
                position++;
                ui_set_cursor(set_x, set_y);
                continue;

            case SPECSCII_TOKEN.ENTER:
                ui_set_cursor(0, cursor_y + 1);
                position++;
                continue;
            
            case SPECSCII_TOKEN.INK:
                position++;
                token_attribute = (token_attribute & 0xf8) | data[position];
                position++;
                continue;
            
            case SPECSCII_TOKEN.INVERT:
                position++;
                mode_inverted = data[position] > 0;
                position++;
                continue;

            case SPECSCII_TOKEN.FLASH:
                position++;
                token_attribute = (token_attribute & 0x7f) | (data[position] << 7);
                position++;
                continue;

            case SPECSCII_TOKEN.PAPER:
                position++;
                token_attribute = (token_attribute & 0xc7) | (data[position] << 3);
                position++;
                continue;
        }

        /* Regular characters */
        if (current_byte >= 0x20 && current_byte <= 0x7f) {
            if (mode_inverted) {
                ui_set_cursor_attribute(zx_swap_attribute(token_attribute));
            } else {
                ui_set_cursor_attribute(token_attribute);
            }
            ui_print_ascii(current_byte);
            position++;
            continue;
        }

        /* Glyphs */
        if (current_byte >= 0x80) {
            if (mode_inverted) {
                ui_set_cursor_attribute(zx_swap_attribute(token_attribute));
            } else {
                ui_set_cursor_attribute(token_attribute);
            }
            ui_print_glyph(data[position]);
            position++;
            continue;
        }

        console.log("Unhandled sequence: ", "0x" + current_byte.toString(16));
        position++;
    }
}

function parse_index(content) {
    var index_type = content.slice(0, 3);
    switch (index_type) {
        /* Default index format */
        case INDEX_TYPES.INDEX:
            if (content.length < 64) {
                throw new Error("IDX malformed");
            }
            return parse_index_IDX(content)
    }
    set_error("Unknown type");
}

function parse_index_IDX(content) {
    var index_data = {
        type: 'IDX',
        page_count: get_idx_hex(content, 0x3, 2),
        link_a: get_idx_page(content, 0x5, 4),
        link_a_txt: get_idx_string(content, 0x9, 9),
        link_b: get_idx_page(content, 0x12, 4),
        link_b_txt: get_idx_string(content, 0x16, 9),
        link_c: get_idx_page(content, 0x1f, 4),
        link_c_txt: get_idx_string(content, 0x23, 9),
        pages: {}
    };

    current_page = -1;
    if (index_data.page_count > 0) {
        current_page = 0;
        for (var page_id = 0; page_id < index_data.page_count; page_id++) {
            var page_start = 0x40 + (page_id * 4)
            index_data.pages[page_id] = {
                type: Number("0x" + content.slice(page_start, page_start+2)),
                parameter: Number("0x" + content.slice(page_start+2, page_start+4))
            }
        }
    }
    current_index = index_data;
    fetch_page();
    return true;
}

/**
 * Set document ID that should be loaded. Return value is used to determine
 * if there were any changes.
 */
function set_document(document_id) {
    if (document_id > DOCUMENT_ZERO) {
        current_document = document_id;
        return true;
    }
    return false;
}

// The function gets called when the window is fully loaded
window.onload = function () {
    // Get the canvas and context
    canvas = document.getElementById("viewport");
    context = canvas.getContext("2d");
    canvas_width = canvas.width;
    canvas_height = canvas.height;
    canvas_image = context.createImageData(canvas_width, canvas_height);

    document.addEventListener('keyup', handleInput);
    function handleInput(event) {
        switch (event.key) {
            case "0":
            case "1":
            case "2":
            case "3":
            case "4":
            case "5":
            case "6":
            case "7":
            case "8":
            case "9":
                current_input = (current_input + event.key).slice(-4);
                break;
            case "Enter":
                var document_id = Number(current_input);
                if (document_id == DOCUMENT_ZERO) {
                    set_document(DOCUMENT_DEFAULT);
                } else {
                    set_document(document_id);
                }
                current_input = "";
                fetch_index();
                break;
            case "Escape":
                current_input = "";
                break;

            case "PageUp":
            case "ArrowUp":
            case "p":
                fetch_page_previous();
                break;

            case "PageDown":
            case "ArrowDown":
            case "n":
                fetch_page_next();
                break;

            case "ArrowLeft":
                if (current_document > PAGE_MINIMUM) {
                    current_document--;
                    fetch_index();
                }
                break;

            case "ArrowRight":
                if (current_document < PAGE_MAXIMUM) {
                    current_document++;
                    fetch_index();
                }
                break;

            /* Link A (Blue) */
            case 'z':
            case 'b': // (b)lue
                if (set_document(get_link_id('link_a'))) {
                    fetch_index();
                }
                break;

            /* Link B (Red) */
            case 'x':
            case 'r': // (r)ed
                if (set_document(get_link_id('link_b'))) {
                    fetch_index();
                }
                break;

            /* Link C (Magenta) */
            case 'c':
            case 'm': // (m)agenta
                if (set_document(get_link_id('link_c'))) {
                    fetch_index();
                }
                break;
        }

        request_render_screen();
    }

    zx_clear_memory(0, STYLE_DEFAULT);
    request_render_screen();
    fetch_index();

    schedule_periodic_refresh();
};