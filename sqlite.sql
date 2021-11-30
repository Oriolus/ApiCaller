CREATE TABLE "http_params" (
	"uid"	text NOT NULL,
	"resource"	text NOT NULL,
	"headers"	text,
	"params"	text,
	PRIMARY KEY("uid")
);

CREATE TABLE "resource" (
	"uid"	TEXT NOT NULL,
	"resource"	TEXT NOT NULL,
	"state"	TEXT NOT NULL,
	"last_update"	INTEGER NOT NULL,
	"last_attempt"	INTEGER,
	"attempt_count"	INTEGER,
	"version"	INTEGER NOT NULL,
	"error"	TEXT,
	PRIMARY KEY("uid")
);
