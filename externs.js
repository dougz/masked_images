/** @type{?function()} */
var puzzle_init;

/** @type{number} */
var wid;

/** @type{Storage} */
var localStorage;

class Message {
    constructor() {
	/** @type{string} */
	this.method;
	/** @type{?string} */
	this.text;
	/** @type{?string} */
	this.logo_url;
	/** @type{?string} */
	this.answer;
        /** @type{Array<string, string>} */
        this.multi;
    }
}
