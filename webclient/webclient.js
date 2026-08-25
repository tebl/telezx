const BASE_URL = "https://raw.githubusercontent.com/tebl/telezx-content/main/out/";

const ASCII_SPACE = 32;
const ATTRIBUTES = {
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

const PAGE_DEFAULT = 1000;
const PAGE_MINIMUM = 1;
const PAGE_MAXIMUM = 9999;
const SCREEN_REFRESH = 1000/50;
const SCREEN_WIDTH_CHARS = 32;
const SCREEN_HEIGHT_CHARS = 24;
const SIZE_DATA = 6144;
const SIZE_ATTR = 768;
const SIZE_MEMORY = SIZE_DATA + SIZE_ATTR;

const STATUS_TYPES = { NONE: -1, OK: 0, ERROR: 1 };
const PAGE_TYPES = { NONE: '', GALLERY: 'GAL', SCREEN: 'SCR', SPECSCII: 'TKN', DEBUG: 'DEV', INDEX: 'IDX' };
const ASSET_TYPES = { TOKEN: 0xaa, SCR: 0x55}

const buffer = new ArrayBuffer(SIZE_MEMORY);
const memory = new Uint8Array(buffer);
const screen_map = zx_calculate_lookup_table();

var cursor_x = 0;
var cursor_y = 0;
var current_font = FONT_DEFAULT;
var current_page = PAGE_DEFAULT;
var current_page_attribute = zx_toAttribute(false, false, ATTRIBUTES.BLACK, ATTRIBUTES.WHITE);
var current_page_type;
var current_subpage = 0;
var current_subpage_max = 1;
var current_input = ""
var current_status = "";
var current_status_type = STATUS_TYPES.NONE;

var current_index = null;
var new_subpage = -1;

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

function ui_setCursor(pos_x, pos_y) {
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

function ui_printBytes(data) {
    zx_setDataAt(cursor_x, cursor_y, data)
    ui_incrementCursor();
}

function ui_printASCII(character) {
    ui_printBytes(ui_getFontData(character - ASCII_SPACE));
}

function ui_getFontData(character) {
    var offset = character*8;
    if (character < 0 || character >= 96) offset = 0;
    return current_font.slice(offset, offset + 8);
}

function ui_printGlyph(character) {
    ui_printBytes(ui_getGlyphData(character - 0x80));
}

function ui_getGlyphData(character) {
    var offset = character*8;
    if (character < 0 || character >= 16) offset = 0;
    return FONT_GLYPHS.slice(offset, offset + 8);
}

function ui_printString(string, attribute) {
    for (var i = 0; i < string.length; i++) {
        if (attribute >= 0) ui_setAttribute(attribute);
        ui_printASCII(string.charCodeAt(i));
    }
}

function zx_setDataAt(pos_x, pos_y, values) {
    var address = screen_map[pos_x][pos_y];
    for (var i = 0; i < 8 && i < values.length; i++) {
        memory[address + i*0x100] = values[i];
    }
}

function ui_setData(values) {
    zx_setDataAt(cursor_x, cursor_y, values);
}

function ui_setFont(font) {
    current_font = font;
}

function zx_setAttributeAt(pos_x, pos_y, value) {
    var index = (pos_y * SCREEN_WIDTH_CHARS) + pos_x;
    memory[SIZE_DATA + index] = value;
}

function ui_setAttribute(value) {
    zx_setAttributeAt(cursor_x, cursor_y, value);
}

function zx_toAttribute(is_flashing, is_bright, paper, ink) {
    return ((is_flashing ? ATTRIBUTES.FLASH : 0x00) | (is_bright ? ATTRIBUTES.BRIGHT : 0x00) | (paper << 3) | ink);
}

function ui_swapAttribute(attribute) {
    parsed = zx_parseAttribute(attribute);
    return zx_toAttribute(
        parsed.flash, 
        parsed.bright,
        parsed.ink,
        parsed.paper
    );
}

function zx_parseAttribute(attribute) {
    return {
        flash: (attribute & ATTRIBUTES.FLASH) == ATTRIBUTES.FLASH,
        bright: (attribute & ATTRIBUTES.BRIGHT) == ATTRIBUTES.BRIGHT,
        paper: (attribute & 0b00111000) >>> 3,
        ink: attribute & 0b00000111
    }
}

function clearCanvas(red, green, blue, alpha) {
    for (var x = 0; x < canvas_width; x++) {
        for (var y = 0; y < canvas_height; y++) {
            // Get the pixel index
            var pixelindex = (y * canvas_width + x) * 4;
            setCanvasIndex(pixelindex, red, green, blue, alpha);
        }
    }
}

function setCanvasIndex(index, red, green, blue, alpha) {
    canvas_image.data[index] = red;
    canvas_image.data[index + 1] = green;
    canvas_image.data[index + 2] = blue;
    canvas_image.data[index + 3] = alpha;
}

function setCanvasPixel(x, y, red, green, blue, alpha) {
    setCanvasIndex((y * canvas_width + x) * 4, red, green, blue, alpha);
}

function getCanvasColour(is_on, attr_value) {
    var colour = (is_on ? attr_value.ink : attr_value.paper);
    if (attr_value.flash && canvas_flash_value) {
        colour = (is_on ? attr_value.paper : attr_value.ink);
    }
    var blue = colour & 1;
    var red = (colour >>> 1) & 1;
    var green = (colour >>> 2) & 1;

    var value = attr_value.bright ? 255 : 224;
    return [
        red * value,
        green * value,
        blue * value
    ];
}

function check_bit(number, bit) {
    var bit_mask = (1 << (7 - bit));
    return (number & bit_mask) != 0;
}

function renderMemory() {
    for (var lot = 0; lot < 3; lot++) {
        for (var line = 0; line < 8; line++) {
            for (var row = 0; row < 8; row++) {
                for (var col = 0; col < SCREEN_WIDTH_CHARS; col++) {
                    var data_idx = lot * 2048 + (line * 8 + row) * SCREEN_WIDTH_CHARS + col;
                    var data_value = memory[data_idx];

                    var attr_idx = lot * 256 + row * SCREEN_WIDTH_CHARS + col;
                    var attr_value = zx_parseAttribute(memory[SIZE_DATA + attr_idx]);

                    for (var bit = 0; bit < 8; bit++) {
                        var x = col * 8 + bit;
                        var y = lot * 64 + row * 8 + line;

                        [red, green, blue] = getCanvasColour(check_bit(data_value, bit), attr_value);
                        setCanvasPixel(x, y, red, green, blue, 255);
                    }
                }
            }
        }
    }
}

function getDateString() {
    var d = new Date();
    return (
        String(d.getDate()).padStart(2, " ") + "." +
        String(d.getMonth() + 1).padStart(2, "0") + " " +
        String(d.getHours()).padStart(2, "0") + ":" +
        String(d.getMinutes()).padStart(2, "0") + ":" +
        String(d.getSeconds()).padStart(2, "0")
    )
}


function setResponse(description, status_type) {
    current_status = description;
    current_status_type = status_type;
}

function setError(description, clear_index = true) {
    setResponse(description, STATUS_TYPES.ERROR);
    if (clear_index) clearIndex();
}

function clearIndex() {
    current_subpage = 0;
    current_subpage_max = 1;
}

function haveStatus() {
    return current_status_type != STATUS_TYPES.NONE;
}

function haveSubpages() {
    return current_subpage_max > 1;
}

function haveSecondaryHeader() {
    return haveStatus() || haveSubpages();
}

function ui_overlayHeaders() {
    ui_setFont(FONT_DEFAULT);
    for (var i = 0; i < SCREEN_WIDTH_CHARS; i++) {
        zx_setAttributeAt(i, 0, zx_toAttribute(false, true, ATTRIBUTES.BLACK, ATTRIBUTES.WHITE));
    }
    ui_setCursor(0, 0);
    ui_printString("P", -1);
    ui_printASCII(ASCII_SPACE);
    if (current_input == '') {
        ui_printString(String(current_page).padStart(4), -1);
    } else {
        ui_printString(current_input.padEnd(4, '-'), (current_input == '' ? -1 : zx_toAttribute(false, false, ATTRIBUTES.BLACK, ATTRIBUTES.GREEN)));
    }
    ui_printASCII(ASCII_SPACE);
    ui_printASCII(ASCII_SPACE);
    ui_printASCII(ASCII_SPACE);
    ui_setFont(FONT_CP850);
    ui_printString("T", zx_toAttribute(false, true, ATTRIBUTES.BLACK, ATTRIBUTES.RED));
    ui_printString("e", zx_toAttribute(false, true, ATTRIBUTES.BLACK, ATTRIBUTES.YELLOW));
    ui_printString("l", zx_toAttribute(false, true, ATTRIBUTES.BLACK, ATTRIBUTES.GREEN));
    ui_printString("e", zx_toAttribute(false, true, ATTRIBUTES.BLACK, ATTRIBUTES.BLUE));
    ui_printString("ZX", -1);
    ui_setFont(FONT_DEFAULT);
    ui_printASCII(ASCII_SPACE);
    ui_printASCII(ASCII_SPACE);
    ui_printASCII(ASCII_SPACE);
    ui_printString(getDateString(), zx_toAttribute(false, false, ATTRIBUTES.BLACK, ATTRIBUTES.YELLOW));
    ui_setFont(FONT_DEFAULT);

    if (haveSecondaryHeader()) {
        ui_setCursor(0, 23);
        var max_chars = haveSubpages() ? (SCREEN_WIDTH_CHARS - 6) : SCREEN_WIDTH_CHARS;
        for (var i = 0; i < max_chars; i++) {
            zx_setAttributeAt(i, 23, zx_toAttribute(false, true, ATTRIBUTES.BLACK, (current_status_type == STATUS_TYPES.ERROR ? ATTRIBUTES.RED : ATTRIBUTES.WHITE)));
            if (i < current_status.length) {
                ui_printASCII(current_status.charCodeAt(i));
            } else {
                ui_printASCII(ASCII_SPACE);
            }
        }

        if (haveSubpages()) {
            ui_printString(
                ' ' + String(current_subpage + 1).padStart(2, '0') + '/' + String(current_subpage_max).padStart(2, '0'), 
                zx_toAttribute(false, true, ATTRIBUTES.BLACK, ATTRIBUTES.GREEN)
            );
        }
    }
}

function renderScreen(timestamp) {
    ui_overlayHeaders();
    renderMemory();

    // Draw the image data to the canvas
    context.putImageData(canvas_image, 0, 0);
}

/* We could call renderScreen directly, but that would lead to an inconsistent
 * framerate so instead we let the browser select a suitable time for us.
 */
function requestRenderScreen() {
    // renderScreen();
    window.requestAnimationFrame(renderScreen);
}

/* Flashing is performed by ZX Spectrum ULA, and should be performed every 32
   frames according to some sites. It'll be prone to drifting though we don't
   really care about that.
*/
function schedulePeriodicRefresh() {
    clearInterval(canvas_interval_id);
    canvas_interval_id = setInterval(
        periodicRefresh, 
        SCREEN_REFRESH
    );
}

function periodicRefresh() {
    canvas_flash_timer++;
    if (canvas_flash_timer > 31) {
        canvas_flash_timer = 0;
        canvas_flash_value = !canvas_flash_value;
    }
    requestRenderScreen();
}

function clearStatus() {
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
function getBaseUrl(page) {
    var padded_id = String(page).padStart(4, "0");
    var index_url = BASE_URL + padded_id + '/' + String(page).padStart(4, "0");
    return index_url;
}

function getAssetUrl(page, subpage, extension) {
    var padded_id = String(subpage).padStart(2, "0");
    return getBaseUrl(page) + '.' + padded_id + extension;
}

function getIndexUrl() {
    return getBaseUrl(current_page) + ".idx";
}

function getScreenUrl(page, subpage) {
    return getAssetUrl(page, subpage, ".scr");
}

function getTokenUrl(page, subpage) {
    return getAssetUrl(page, subpage, ".tkn");
}

function fetchIndex() {
    switch (current_page) {
        case 9999:
            setDebugIndex();
            return;
    }

    fetchRemoteIndex();
}

async function fetchRemoteIndex() {
    try {
        // Fetch the JSON file  
        const response = await fetch(getIndexUrl());

        // Check for HTTP errors  
        if (!response.ok) {
            throw new Error(`${response.status} ${response.statusText}`);
        }

        // Parse JSON data  
        const content = await response.text();
        if (content.length >= 3) {
            parseIndex(content);
        } else {
            setError("Empty index");
        }
    } catch (error) {
        setError(error.message);
        console.error("Failed to fetch data:", error);
    }

    requestRenderScreen();
}

function fetchCurrent() {
    switch (current_page_type) {
        case PAGE_TYPES.DEBUG:
            generatePage(current_page, current_subpage);
            break;

        case PAGE_TYPES.GALLERY:
            fetch_scr_asset(current_page, current_subpage);
            break;
        
        case PAGE_TYPES.SPECSCII:
            fetch_token_asset(current_page, current_subpage, current_page_attribute);
            break;

        case PAGE_TYPES.SCREEN:
            fetch_scr_asset(current_page, -1);
            break;
    }
}

function fetchPage() {
    var page = null;
    if (current_index == null) return generate_blank_page();
    if (new_subpage in current_index.pages) page = current_index.pages[new_subpage];
    if (page == null) return generate_blank_page();
    
    if (page.type == ASSET_TYPES.TOKEN) {
        return fetch_token_asset(
            current_page, 
            current_subpage, 
            page.extra);
    }
    if (page.type == ASSET_TYPES.SCR) {
        return fetch_scr_asset(
            current_page, 
            current_subpage);
    }
    return generate_blank_page();
}

function generate_blank_page() {
    zx_clear_memory(0x00, zx_toAttribute(false, false, ATTRIBUTES.YELLOW, ATTRIBUTES.RED))
    setResponse(String(page), STATUS_TYPES.OK);
    requestRenderScreen();
    return true;
}

function setDebugIndex() {
    current_subpage = 0;
    current_subpage_max = 3;
    current_page_type = PAGE_TYPES.DEBUG;
    fetchCurrent();
}

function generatePage(page, subpage) {
    zx_clear_memory(0x00, zx_toAttribute(false, false, ATTRIBUTES.BLACK, ATTRIBUTES.WHITE))

    switch (subpage) {
        case 0:
            ui_setCursor(0, 2);
            ui_setFont(FONT_DEFAULT);
            ui_printString("Default:", zx_toAttribute(false, true, ATTRIBUTES.BLACK, ATTRIBUTES.YELLOW));
            ui_setCursor(0, 3);
            ui_setFont(FONT_DEFAULT);
            for (let i = 0; i < (FONT_DEFAULT.length / 8); i++) {
                ui_printBytes(ui_getFontData(i));
            }

            ui_setCursor(0, 7);
            ui_setFont(FONT_DEFAULT);
            ui_printString("Computer:", zx_toAttribute(false, true, ATTRIBUTES.BLACK, ATTRIBUTES.YELLOW));
            ui_setCursor(0, 8);
            ui_setFont(FONT_CP850);
            for (let i = 0; i < (FONT_DEFAULT.length / 8); i++) {
                ui_printBytes(ui_getFontData(i));
            }
            break;
        case 1:
        case 2:
            let x = 1;
            let y = 2;
            let start = (subpage == 1 ? 0 : 0xc8);
            let end = (subpage == 1 ? 0xc7 : 0xff);
            for (let i = start; i <= end; i++) {
                ui_setCursor(x, y);
                ui_printString(i.toString(16).padStart(2, '0'), i);
                y++;
                if (y >= (SCREEN_HEIGHT_CHARS - 2)) {
                    y = 2;
                    x += 3;
                }
            }
            break;
    }

    setResponse(String(page), STATUS_TYPES.OK);
    requestRenderScreen();
}

function fetchNext() {
    if (current_subpage < (current_subpage_max - 1)) {
        current_subpage++;
        fetchCurrent();
    }
}

function fetchPrevious() {
    if (current_subpage > 0) {
        current_subpage--;
        fetchCurrent();
    }
}

async function fetch_scr_asset(page, subpage) {
    try {
        // Fetch the JSON file  
        const fetch_url = getScreenUrl(page, subpage);
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
            setError("Not SCR");
            console.error("Data not consistent with SCR:", data.length);
        }

        clearStatus();
    } catch (error) {
        console.error("Failed to fetch data:", error);
        setError(error.message);
    }

    requestRenderScreen();
}

async function fetch_token_asset(page, subpage, default_attribute) {
    try {
        // Fetch the JSON file  
        const fetch_url = getTokenUrl(page, subpage);
        const response = await fetch(fetch_url);

        // Check for HTTP errors  
        if (!response.ok) {
            throw new Error(`${response.status} ${response.statusText}`);
        }

        // Parse JSON data  
        const data = await response.bytes();
        processTokens(data, default_attribute);
    
        clearStatus();
    } catch (error) {
        console.error("Failed to fetch data:", error);
        setError(error.message, false);
        return;
    }

    requestRenderScreen();
}


const SPECSCII = {
    ENTER: 0x0d,
    INK: 0x10,
    PAPER: 0x11,
    FLASH: 0x12,
    BRIGHT: 0x13,
    INVERT: 0x14,
    CURSOR: 0x16
};

function processTokens(data, default_attribute) {
    zx_clear_memory(0x00, default_attribute)

    ui_setCursor(0, 0);
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
            case SPECSCII.BRIGHT:
                position++;
                token_attribute = (token_attribute & 0xbf) | (data[position] << 6);
                position++;
                continue;
            
            case SPECSCII.CURSOR:
                position++;
                const set_y = data[position];
                position++;
                const set_x = data[position];
                position++;
                ui_setCursor(set_x, set_y);
                continue;

            case SPECSCII.ENTER:
                ui_setCursor(0, cursor_y + 1);
                position++;
                continue;
            
            case SPECSCII.INK:
                position++;
                token_attribute = (token_attribute & 0xf8) | data[position];
                position++;
                continue;
            
            case SPECSCII.INVERT:
                position++;
                mode_inverted = data[position] > 0;
                position++;
                continue;

            case SPECSCII.FLASH:
                position++;
                token_attribute = (token_attribute & 0x7f) | (data[position] << 7);
                position++;
                continue;

            case SPECSCII.PAPER:
                position++;
                token_attribute = (token_attribute & 0xc7) | (data[position] << 3);
                position++;
                continue;
        }

        if (current_byte >= 0x20 && current_byte <= 0x7f) {
            if (mode_inverted) {
                ui_setAttribute(ui_swapAttribute(token_attribute));
            } else {
                ui_setAttribute(token_attribute);
            }
            ui_printASCII(current_byte);
            position++;
            continue;
        }

        if (current_byte >= 0x80) {
            if (mode_inverted) {
                ui_setAttribute(ui_swapAttribute(token_attribute));
            } else {
                ui_setAttribute(token_attribute);
            }
            ui_printGlyph(data[position]);
            position++;
            continue;
        }

        console.log("Unhandled sequence: ", "0x" + current_byte.toString(16));
        position++;
    }
}

function parseIndex(content) {
    current_subpage = 0;
    current_subpage_max = 1;
    var type = content.slice(0, 3);
    switch (type) {
        // /* Gallery */
        // case PAGE_TYPES.GALLERY:
        //     if (content.length < 5) {
        //         throw new Error("GAL malformed");
        //     }
        //     setResponse(content.slice(0, 3) + " " + content.slice(3, 5), STATUS_TYPES.OK);
        //     return parseGAL(content);

        // /* Single screen */
        // case PAGE_TYPES.SCREEN:
        //     setResponse(content.slice(0, 3), STATUS_TYPES.OK);
        //     return parseSCR(content);
        
        // /* SPECSCII tokens */
        // case PAGE_TYPES.SPECSCII:
        //     if (content.length < 7) {
        //         throw new Error("TKN malformed");
        //     }
        //     setResponse(content.slice(0, 3), STATUS_TYPES.OK);
        //     return parseTKN(content);
        
        /* Default index format */
        case PAGE_TYPES.INDEX:
            if (content.length < 64) {
                throw new Error("IDX malformed");
            }
            return parseIDX(content)
    }
    setError("Unknown type");
}

// function parseGAL(content) {
//     current_page_type = PAGE_TYPES.GALLERY;
//     current_subpage_max = Number("0x" + content.slice(3, 5));
//     fetchCurrent();
//     return true;
// }

function parseIDX(content) {
    var index_data = {
        type: 'IDX',
        page_count: Number("0x" + content.slice(3, 5)),
        link_a: get_idx_string(content, 5, 4),
        link_a_txt: get_idx_string(content, 9, 9),
        link_b: get_idx_string(content, 0x12, 4),
        link_b_txt: get_idx_string(content, 0x16, 9),
        link_c: get_idx_string(content, 0x1f, 4),
        link_c_txt: get_idx_string(content, 0x23, 9),
        pages: {}
    };

    new_subpage = -1;
    if (index_data.page_count > 0) {
        new_subpage = 0;
        for (var page_id = 0; page_id < index_data.page_count; page_id++) {
            var page_start = 0x40 + (page_id * 4)
            index_data.pages[page_id] = {
                type: Number("0x" + content.slice(page_start, page_start+2)),
                extra: Number("0x" + content.slice(page_start+2, page_start+4))
            }
        }
    }
    current_index = index_data;
    fetchPage();
    return true;
}

function get_idx_string(content, start, num_bytes) {
    return content.slice(start, start + num_bytes).replace(/\0.*$/g,'');
}

// function parseSCR(content) {
//     current_page_type = PAGE_TYPES.SCREEN;
//     fetchCurrent();
//     return true;
// }

// function parseTKN(content) {
//     current_page_type = PAGE_TYPES.SPECSCII;
//     current_subpage_max = Number("0x" + content.slice(3, 5));
//     current_page_attribute = Number("0x" + content.slice(5, 7));
//     fetchCurrent();
//     return true;
// }

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
                var next_page = Number(current_input);
                if (next_page == 0) {
                    next_page = PAGE_DEFAULT;
                }
                current_page = next_page;
                current_input = "";
                fetchIndex();
                break;
            case "Escape":
                current_input = "";
                break;

            case "PageUp":
            case "ArrowUp":
            case "p":
                fetchPrevious();
                break;

            case "PageDown":
            case "ArrowDown":
            case "n":
                fetchNext();
                break;

            case "ArrowLeft":
                current_page--;
                if (current_page < PAGE_MINIMUM) current_page = PAGE_MINIMUM;
                fetchIndex();
                break;

            case "ArrowRight":
                current_page++;
                if (current_page > PAGE_MAXIMUM) current_page = PAGE_MAXIMUM;
                fetchIndex();
                break;

            }

        requestRenderScreen();
    }

    zx_clear_memory(0, zx_toAttribute(false, true, ATTRIBUTES.BLACK, ATTRIBUTES.WHITE));
    requestRenderScreen();
    fetchIndex();

    schedulePeriodicRefresh();
};