--
-- PostgreSQL database dump
--

-- Dumped from database version 12.22 (Ubuntu 12.22-0ubuntu0.20.04.4)
-- Dumped by pg_dump version 12.22 (Ubuntu 12.22-0ubuntu0.20.04.4)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: lab_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO lab_user;

--
-- Name: cubicle; Type: TABLE; Schema: public; Owner: lab_user
--

CREATE TABLE public.cubicle (
    id integer NOT NULL,
    number character varying(10) NOT NULL,
    room_lab_id integer NOT NULL,
    student_roll character varying(20)
);


ALTER TABLE public.cubicle OWNER TO lab_user;

--
-- Name: cubicle_id_seq; Type: SEQUENCE; Schema: public; Owner: lab_user
--

CREATE SEQUENCE public.cubicle_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cubicle_id_seq OWNER TO lab_user;

--
-- Name: cubicle_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: lab_user
--

ALTER SEQUENCE public.cubicle_id_seq OWNED BY public.cubicle.id;


--
-- Name: equipment; Type: TABLE; Schema: public; Owner: lab_user
--

CREATE TABLE public.equipment (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    category character varying(50) NOT NULL,
    manufacturer character varying(100),
    model character varying(100),
    serial_number character varying(100) NOT NULL,
    invoice_number character varying(100),
    cost_per_unit double precision,
    location character varying(100),
    po_date character varying(20),
    purchase_date character varying(20),
    warranty_expiry character varying(20),
    status character varying(20),
    intender_name character varying(100),
    remarks character varying(200),
    quantity integer,
    department_code character varying(100),
    mac_address character varying(50),
    assigned_to_roll character varying(20),
    assigned_by character varying(100),
    assigned_date timestamp without time zone
);


ALTER TABLE public.equipment OWNER TO lab_user;

--
-- Name: equipment_history; Type: TABLE; Schema: public; Owner: lab_user
--

CREATE TABLE public.equipment_history (
    id integer NOT NULL,
    equipment_id integer NOT NULL,
    assigned_to_roll character varying(20),
    assigned_by character varying(100),
    assigned_date timestamp without time zone,
    unassigned_date timestamp without time zone,
    status_snapshot character varying(50),
    "timestamp" timestamp without time zone
);


ALTER TABLE public.equipment_history OWNER TO lab_user;

--
-- Name: equipment_history_id_seq; Type: SEQUENCE; Schema: public; Owner: lab_user
--

CREATE SEQUENCE public.equipment_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.equipment_history_id_seq OWNER TO lab_user;

--
-- Name: equipment_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: lab_user
--

ALTER SEQUENCE public.equipment_history_id_seq OWNED BY public.equipment_history.id;


--
-- Name: equipment_id_seq; Type: SEQUENCE; Schema: public; Owner: lab_user
--

CREATE SEQUENCE public.equipment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.equipment_id_seq OWNER TO lab_user;

--
-- Name: equipment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: lab_user
--

ALTER SEQUENCE public.equipment_id_seq OWNED BY public.equipment.id;


--
-- Name: provisioning_request; Type: TABLE; Schema: public; Owner: lab_user
--

CREATE TABLE public.provisioning_request (
    id integer NOT NULL,
    mac_address character varying(32) NOT NULL,
    ip_address character varying(32) NOT NULL,
    os_image character varying(64) NOT NULL,
    "timestamp" timestamp without time zone
);


ALTER TABLE public.provisioning_request OWNER TO lab_user;

--
-- Name: provisioning_request_id_seq; Type: SEQUENCE; Schema: public; Owner: lab_user
--

CREATE SEQUENCE public.provisioning_request_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.provisioning_request_id_seq OWNER TO lab_user;

--
-- Name: provisioning_request_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: lab_user
--

ALTER SEQUENCE public.provisioning_request_id_seq OWNED BY public.provisioning_request.id;


--
-- Name: room_lab; Type: TABLE; Schema: public; Owner: lab_user
--

CREATE TABLE public.room_lab (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    capacity integer NOT NULL,
    staff_incharge character varying(100)
);


ALTER TABLE public.room_lab OWNER TO lab_user;

--
-- Name: room_lab_id_seq; Type: SEQUENCE; Schema: public; Owner: lab_user
--

CREATE SEQUENCE public.room_lab_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.room_lab_id_seq OWNER TO lab_user;

--
-- Name: room_lab_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: lab_user
--

ALTER SEQUENCE public.room_lab_id_seq OWNED BY public.room_lab.id;


--
-- Name: slurm_account; Type: TABLE; Schema: public; Owner: lab_user
--

CREATE TABLE public.slurm_account (
    id integer NOT NULL,
    roll character varying(20) NOT NULL,
    status character varying(20) NOT NULL
);


ALTER TABLE public.slurm_account OWNER TO lab_user;

--
-- Name: slurm_account_id_seq; Type: SEQUENCE; Schema: public; Owner: lab_user
--

CREATE SEQUENCE public.slurm_account_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.slurm_account_id_seq OWNER TO lab_user;

--
-- Name: slurm_account_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: lab_user
--

ALTER SEQUENCE public.slurm_account_id_seq OWNED BY public.slurm_account.id;


--
-- Name: student; Type: TABLE; Schema: public; Owner: lab_user
--

CREATE TABLE public.student (
    roll character varying(20) NOT NULL,
    name character varying(100) NOT NULL,
    course character varying(20),
    year character varying(10),
    joining_year character varying(10),
    faculty character varying(100),
    email character varying(100),
    phone character varying(20),
    user_id integer NOT NULL
);


ALTER TABLE public.student OWNER TO lab_user;

--
-- Name: user; Type: TABLE; Schema: public; Owner: lab_user
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    email character varying(150) NOT NULL,
    password character varying(255) NOT NULL,
    role character varying(20) NOT NULL,
    is_approved boolean,
    reset_token character varying(200),
    reset_token_expiry timestamp without time zone,
    registered_at timestamp without time zone,
    approved_at timestamp without time zone,
    is_active boolean
);


ALTER TABLE public."user" OWNER TO lab_user;

--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: lab_user
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_id_seq OWNER TO lab_user;

--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: lab_user
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- Name: workstation_asset; Type: TABLE; Schema: public; Owner: lab_user
--

CREATE TABLE public.workstation_asset (
    id integer NOT NULL,
    manufacturer character varying(100),
    "otherManufacturer" character varying(100),
    model character varying(100),
    serial character varying(100),
    os character varying(50),
    "otherOs" character varying(50),
    processor character varying(100),
    cores character varying(10),
    ram character varying(20),
    "otherRam" character varying(20),
    storage_type1 character varying(50),
    storage_capacity1 character varying(20),
    storage_type2 character varying(50),
    storage_capacity2 character varying(20),
    gpu character varying(100),
    vram character varying(10),
    keyboard_provided character varying(10),
    keyboard_details character varying(100),
    mouse_provided character varying(10),
    mouse_details character varying(100),
    monitor_provided character varying(20),
    monitor_details character varying(100),
    monitor_size character varying(10),
    monitor_serial character varying(100),
    mac_address character varying(50),
    po_date character varying(20),
    source_of_fund character varying(100),
    status character varying(20),
    location character varying(100),
    indenter character varying(100),
    department_code character varying(200)
);


ALTER TABLE public.workstation_asset OWNER TO lab_user;

--
-- Name: workstation_asset_id_seq; Type: SEQUENCE; Schema: public; Owner: lab_user
--

CREATE SEQUENCE public.workstation_asset_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workstation_asset_id_seq OWNER TO lab_user;

--
-- Name: workstation_asset_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: lab_user
--

ALTER SEQUENCE public.workstation_asset_id_seq OWNED BY public.workstation_asset.id;


--
-- Name: workstation_assignment; Type: TABLE; Schema: public; Owner: lab_user
--

CREATE TABLE public.workstation_assignment (
    id integer NOT NULL,
    workstation_id integer NOT NULL,
    student_roll character varying(20) NOT NULL,
    issue_date character varying(20) NOT NULL,
    system_required_till character varying(20) NOT NULL,
    end_date character varying(20),
    remarks character varying(200),
    is_active boolean
);


ALTER TABLE public.workstation_assignment OWNER TO lab_user;

--
-- Name: workstation_assignment_id_seq; Type: SEQUENCE; Schema: public; Owner: lab_user
--

CREATE SEQUENCE public.workstation_assignment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workstation_assignment_id_seq OWNER TO lab_user;

--
-- Name: workstation_assignment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: lab_user
--

ALTER SEQUENCE public.workstation_assignment_id_seq OWNED BY public.workstation_assignment.id;


--
-- Name: cubicle id; Type: DEFAULT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.cubicle ALTER COLUMN id SET DEFAULT nextval('public.cubicle_id_seq'::regclass);


--
-- Name: equipment id; Type: DEFAULT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.equipment ALTER COLUMN id SET DEFAULT nextval('public.equipment_id_seq'::regclass);


--
-- Name: equipment_history id; Type: DEFAULT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.equipment_history ALTER COLUMN id SET DEFAULT nextval('public.equipment_history_id_seq'::regclass);


--
-- Name: provisioning_request id; Type: DEFAULT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.provisioning_request ALTER COLUMN id SET DEFAULT nextval('public.provisioning_request_id_seq'::regclass);


--
-- Name: room_lab id; Type: DEFAULT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.room_lab ALTER COLUMN id SET DEFAULT nextval('public.room_lab_id_seq'::regclass);


--
-- Name: slurm_account id; Type: DEFAULT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.slurm_account ALTER COLUMN id SET DEFAULT nextval('public.slurm_account_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Name: workstation_asset id; Type: DEFAULT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.workstation_asset ALTER COLUMN id SET DEFAULT nextval('public.workstation_asset_id_seq'::regclass);


--
-- Name: workstation_assignment id; Type: DEFAULT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.workstation_assignment ALTER COLUMN id SET DEFAULT nextval('public.workstation_assignment_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: lab_user
--

COPY public.alembic_version (version_num) FROM stdin;
ce00d36ff32f
\.


--
-- Data for Name: cubicle; Type: TABLE DATA; Schema: public; Owner: lab_user
--

COPY public.cubicle (id, number, room_lab_id, student_roll) FROM stdin;
1	1	1	123444
2	2	1	\N
3	3	1	cs25phd11221
4	4	1	\N
5	5	1	\N
6	6	1	\N
7	7	1	\N
8	8	1	\N
9	9	1	\N
10	10	1	cs25btech13001
11	11	1	\N
12	12	1	\N
13	13	1	\N
14	14	1	\N
15	15	1	\N
16	16	1	\N
17	17	1	\N
18	18	1	\N
19	19	1	\N
20	20	1	\N
21	21	1	cs23mtech12001
22	22	1	\N
23	23	1	\N
24	24	1	\N
25	25	1	\N
26	26	1	\N
27	27	1	\N
28	28	1	\N
29	29	1	\N
30	30	1	\N
31	31	1	\N
32	32	1	\N
33	33	1	\N
34	34	1	\N
35	35	1	\N
36	36	1	\N
37	37	1	\N
38	38	1	cs25btech11001
39	39	1	cs25btech15001
40	40	1	\N
41	41	1	\N
42	42	1	\N
43	43	1	cs25mtech11001
44	1	2	\N
45	2	2	\N
46	3	2	cs25mtech12010
47	4	2	\N
48	5	2	\N
49	6	2	\N
50	7	2	\N
51	8	2	\N
52	9	2	\N
53	10	2	\N
54	11	2	\N
55	12	2	\N
56	13	2	\N
57	14	2	\N
58	15	2	\N
59	16	2	\N
60	17	2	\N
61	18	2	\N
62	19	2	\N
63	20	2	\N
64	21	2	\N
65	1	3	\N
66	2	3	\N
67	3	3	\N
68	4	3	\N
69	5	3	\N
70	6	3	\N
71	7	3	\N
72	8	3	\N
73	9	3	\N
74	10	3	\N
75	11	3	\N
76	12	3	\N
77	13	3	\N
78	14	3	\N
79	15	3	\N
80	16	3	\N
81	17	3	\N
82	18	3	\N
83	19	3	\N
84	20	3	\N
85	21	3	\N
86	22	3	\N
87	23	3	\N
88	24	3	\N
89	25	3	\N
90	26	3	\N
91	27	3	\N
92	28	3	\N
93	29	3	\N
94	30	3	\N
95	31	3	\N
96	32	3	\N
97	33	3	\N
98	34	3	\N
99	35	3	\N
100	36	3	\N
101	37	3	\N
102	38	3	\N
103	39	3	\N
104	40	3	\N
105	41	3	\N
106	42	3	\N
107	43	3	\N
108	44	3	\N
109	45	3	\N
110	46	3	\N
111	47	3	\N
112	48	3	\N
113	49	3	\N
114	50	3	\N
115	51	3	\N
116	52	3	\N
117	53	3	\N
118	54	3	\N
119	55	3	\N
120	56	3	\N
121	57	3	\N
122	58	3	\N
123	59	3	\N
124	60	3	\N
125	61	3	\N
126	62	3	\N
127	63	3	\N
128	64	3	\N
129	65	3	\N
130	66	3	\N
131	67	3	\N
132	68	3	\N
133	69	3	\N
134	70	3	\N
135	71	3	\N
136	72	3	\N
137	73	3	\N
138	74	3	\N
139	75	3	\N
140	76	3	\N
141	77	3	\N
142	78	3	\N
143	79	3	\N
144	80	3	\N
145	81	3	\N
146	82	3	\N
147	83	3	\N
148	84	3	\N
149	85	3	\N
150	86	3	\N
151	87	3	\N
152	88	3	\N
153	89	3	\N
154	90	3	\N
155	91	3	\N
156	92	3	\N
157	93	3	\N
158	94	3	\N
159	95	3	\N
160	96	3	\N
161	97	3	\N
162	98	3	\N
163	99	3	\N
164	100	3	\N
165	101	3	\N
166	102	3	\N
167	103	3	\N
168	104	3	\N
169	105	3	\N
170	106	3	\N
171	107	3	\N
172	108	3	\N
173	109	3	\N
174	110	3	\N
175	111	3	\N
176	112	3	\N
177	113	3	\N
178	114	3	\N
179	1	4	\N
180	2	4	\N
181	3	4	\N
182	4	4	\N
183	5	4	\N
184	6	4	\N
185	7	4	\N
186	8	4	\N
187	9	4	\N
188	10	4	\N
189	11	4	\N
190	12	4	\N
191	13	4	\N
192	14	4	\N
193	15	4	\N
194	16	4	\N
195	17	4	\N
196	18	4	\N
197	19	4	\N
198	20	4	\N
199	21	4	\N
200	22	4	\N
201	23	4	\N
202	24	4	\N
203	25	4	\N
204	26	4	\N
205	27	4	\N
206	28	4	\N
207	29	4	\N
208	30	4	\N
209	1	5	\N
210	2	5	\N
211	3	5	\N
212	4	5	\N
213	5	5	\N
214	6	5	\N
215	7	5	\N
216	8	5	\N
217	9	5	\N
218	10	5	\N
219	11	5	\N
220	12	5	\N
221	13	5	\N
222	14	5	\N
223	15	5	\N
224	16	5	\N
225	17	5	\N
226	18	5	\N
227	19	5	\N
228	20	5	\N
229	21	5	\N
230	22	5	\N
231	23	5	\N
232	24	5	\N
233	25	5	\N
234	1	6	cs25btech12001
235	2	6	\N
236	3	6	\N
237	4	6	\N
238	5	6	\N
239	6	6	\N
240	7	6	\N
241	8	6	\N
242	9	6	\N
243	10	6	\N
244	11	6	\N
245	12	6	\N
246	13	6	\N
247	14	6	\N
248	15	6	\N
249	16	6	\N
250	17	6	\N
251	18	6	\N
252	19	6	\N
253	20	6	\N
254	21	6	\N
255	22	6	\N
256	23	6	\N
257	24	6	\N
258	25	6	\N
259	26	6	\N
260	27	6	\N
261	28	6	\N
262	29	6	\N
263	30	6	\N
264	31	6	\N
265	32	6	\N
266	33	6	\N
267	34	6	\N
268	35	6	\N
269	36	6	\N
270	37	6	\N
271	38	6	\N
272	39	6	\N
273	40	6	\N
274	41	6	\N
275	42	6	\N
276	43	6	\N
277	44	6	\N
278	45	6	\N
279	46	6	\N
280	47	6	\N
281	48	6	\N
282	49	6	\N
283	50	6	\N
284	51	6	\N
285	52	6	\N
286	53	6	\N
287	54	6	\N
288	55	6	\N
289	56	6	\N
290	57	6	\N
291	58	6	\N
292	59	6	\N
293	60	6	\N
294	61	6	\N
295	62	6	\N
296	63	6	\N
297	64	6	\N
298	65	6	\N
299	66	6	\N
300	67	6	\N
301	68	6	\N
302	69	6	\N
303	70	6	\N
304	71	6	\N
305	72	6	\N
306	73	6	\N
307	74	6	\N
308	75	6	\N
309	76	6	\N
310	77	6	\N
311	78	6	\N
312	79	6	\N
313	80	6	\N
314	81	6	\N
315	82	6	\N
316	83	6	\N
317	84	6	\N
318	85	6	\N
319	86	6	\N
320	87	6	\N
321	88	6	\N
322	89	6	\N
323	90	6	\N
324	91	6	\N
325	92	6	\N
326	93	6	\N
327	94	6	\N
328	95	6	\N
329	96	6	\N
330	97	6	\N
331	98	6	\N
332	99	6	\N
333	100	6	\N
334	101	6	\N
335	102	6	\N
336	103	6	\N
337	104	6	\N
338	105	6	\N
339	106	6	\N
340	107	6	\N
341	108	6	\N
342	109	6	\N
343	110	6	\N
344	111	6	\N
345	112	6	\N
346	113	6	\N
347	114	6	\N
348	115	6	\N
349	116	6	\N
350	117	6	\N
351	118	6	\N
352	119	6	\N
353	120	6	\N
354	121	6	\N
355	122	6	\N
356	123	6	\N
357	124	6	\N
358	125	6	\N
359	126	6	\N
360	127	6	\N
361	128	6	\N
362	129	6	\N
363	130	6	\N
364	131	6	\N
365	132	6	\N
366	133	6	\N
367	134	6	\N
368	135	6	\N
369	136	6	\N
370	137	6	\N
371	138	6	\N
372	139	6	\N
373	140	6	\N
374	141	6	\N
375	142	6	\N
376	1	7	cs25mtech11003
377	2	7	\N
378	3	7	\N
379	4	7	\N
380	5	7	\N
381	6	7	\N
382	7	7	\N
383	8	7	\N
384	9	7	\N
385	10	7	\N
386	11	7	\N
387	12	7	\N
388	13	7	\N
389	14	7	\N
390	15	7	\N
391	16	7	\N
392	17	7	\N
393	18	7	\N
394	19	7	\N
395	20	7	\N
396	21	7	\N
397	22	7	\N
398	23	7	\N
399	24	7	\N
400	25	7	\N
401	1	8	\N
402	2	8	\N
403	3	8	\N
404	4	8	\N
405	5	8	\N
406	6	8	\N
407	7	8	\N
408	8	8	\N
409	9	8	\N
410	10	8	\N
411	11	8	\N
412	12	8	\N
413	13	8	\N
414	14	8	\N
415	15	8	\N
416	16	8	\N
417	17	8	\N
418	18	8	\N
419	19	8	\N
420	20	8	\N
421	21	8	\N
422	22	8	\N
423	23	8	\N
424	24	8	\N
425	25	8	\N
426	1	9	cs25phd11011
428	3	9	\N
429	4	9	\N
430	5	9	\N
431	6	9	\N
432	7	9	\N
433	8	9	\N
434	9	9	\N
435	10	9	\N
436	11	9	\N
437	12	9	\N
438	13	9	\N
439	14	9	\N
440	15	9	\N
441	16	9	\N
442	17	9	\N
443	18	9	\N
444	19	9	\N
445	20	9	\N
446	21	9	\N
447	22	9	\N
448	23	9	\N
449	24	9	\N
450	25	9	\N
451	26	9	\N
452	27	9	\N
453	28	9	\N
454	29	9	\N
455	30	9	\N
456	31	9	\N
457	32	9	\N
458	1	10	cs25btech11000
459	2	10	\N
460	3	10	\N
461	4	10	\N
462	5	10	\N
463	6	10	\N
464	7	10	\N
465	8	10	\N
466	9	10	\N
467	10	10	\N
468	11	10	\N
469	12	10	\N
470	13	10	\N
471	14	10	\N
472	15	10	\N
473	16	10	\N
474	17	10	\N
475	18	10	\N
476	19	10	\N
477	20	10	cs24mtech12004
478	21	10	\N
479	22	10	\N
480	23	10	\N
481	24	10	\N
482	25	10	\N
483	26	10	\N
484	27	10	\N
485	1	11	\N
486	2	11	cs25mtech12001
487	3	11	\N
488	4	11	\N
489	5	11	\N
490	6	11	\N
491	7	11	\N
492	8	11	\N
493	9	11	\N
494	10	11	\N
495	11	11	\N
496	12	11	\N
497	13	11	\N
498	14	11	\N
499	15	11	\N
500	16	11	\N
501	17	11	\N
502	18	11	\N
503	19	11	\N
504	20	11	\N
505	21	11	\N
506	22	11	\N
507	23	11	\N
508	24	11	\N
509	25	11	\N
510	1	12	cs25btech14001
512	3	12	\N
513	4	12	\N
514	5	12	\N
515	6	12	\N
516	7	12	\N
517	8	12	\N
518	9	12	\N
519	10	12	\N
520	11	12	\N
521	12	12	\N
522	13	12	\N
523	14	12	\N
524	15	12	\N
525	16	12	\N
526	17	12	\N
527	18	12	\N
528	19	12	\N
529	20	12	\N
530	21	12	\N
531	22	12	\N
532	23	12	\N
533	24	12	\N
534	25	12	\N
535	26	12	\N
536	27	12	\N
537	28	12	\N
538	29	12	\N
539	30	12	\N
540	31	12	\N
541	32	12	\N
542	33	12	\N
\.


--
-- Data for Name: equipment; Type: TABLE DATA; Schema: public; Owner: lab_user
--

COPY public.equipment (id, name, category, manufacturer, model, serial_number, invoice_number, cost_per_unit, location, po_date, purchase_date, warranty_expiry, status, intender_name, remarks, quantity, department_code, mac_address, assigned_to_roll, assigned_by, assigned_date) FROM stdin;
1	Dell Power EDGE	Server	Dell	SYS-621C-TN12R	AX102344511112	12/12/811113	256000	CS-107	2025-07-28	2025-08-11	2025-08-31	Available	Dr. Praveen Tammana	\N	1	CSE/20250728/Server/Dell/Praveen/001	\N	\N	admin@cse.iith.ac.in	2025-09-02 01:17:27.412956
2	Dell Power EDGE	Server	Dell	SYS-621C-TN12R	AX102344511113	12/12/811113	256000	CS-107	2025-07-28	2025-08-11	2025-08-31	Issued	Dr. Praveen Tammana	\N	1	CSE/20250728/Server/Dell/Praveen/002	\N	cs24mtech12004	admin@cse.iith.ac.in	2025-09-01 15:53:35.809184
3	Dell Monitor	Monitor	Dell	234512	AX345671	12/12/812345	8000	CS-108	2025-07-28	2025-08-05	2025-08-31	Available	Dr. Rajesh Kedia	\N	1	CSE/20250728/Monitor/Dell/Rajesh/001	\N	\N	admin@cse.iith.ac.in	2025-09-02 01:18:02.168748
4	Dell Monitor	Monitor	Dell	234512	AX345672	12/12/812345	8000	CS-108	2025-07-28	2025-08-05	2025-08-31	Available	Dr. Rajesh Kedia	\N	1	CSE/20250728/Monitor/Dell/Rajesh/002	\N	\N	admin@cse.iith.ac.in	2025-09-01 15:19:08.339109
5	Dell Monitor	Monitor	Dell	234512	AX345673	12/12/812345	8000	CS-108	2025-07-28	2025-08-05	2025-08-31	Available	Dr. Rajesh Kedia	\N	1	CSE/20250728/Monitor/Dell/Rajesh/003	\N	\N	admin@cse.iith.ac.in	2025-09-01 06:47:12.079126
6	NIC Card 10G	NIC card	Gigabyte	qwe11	abc123	1111qqq	12000	CS-107	2025-07-28	2025-08-06	2028-12-21	Issued	Dr. Rajesh Kedia	\N	1	CSE/20250728/NIC card/Gigabyte/Rajesh/001	\N	cs25btech11001	admin@cse.iith.ac.in	2025-08-31 12:39:23.978774
7	HP Laser Jet Printer	Printer	HP	1200	abc123234	1111qqqew	24000	CS-108	2025-07-28	2025-08-06	2028-12-23	Issued	Dr. Rajesh Kedia	\N	1	CSE/20250728/Printer/HP/Rajesh/001	\N	cs23mtech12001	admin@cse.iith.ac.in	2025-09-01 06:47:02.837106
8	Dell PowerEdge 112	Server	Dell	SYS-111E-WR11	AX10234451q	12/12/8111123	850000	CS-208	2025-08-22	2025-08-23	2027-10-13	Available	Prof. Maunendra Sankar Desarkar	\N	1	CSE/20250822/Server/Dell/Maunendra/003	\N	\N	\N	\N
9	Dell PowerEdge 112	Server	Dell	SYS-111E-WR11	AX10234451w	12/12/8111123	850000	CS-208	2025-08-22	2025-08-23	2027-10-13	Available	Prof. Maunendra Sankar Desarkar	\N	1	CSE/20250822/Server/Dell/Maunendra/004	\N	\N	\N	\N
10	NVDIA	GPU	Nvidia	rtx 6000	234908	12/89/09	250000	CS-109	2025-07-28	2025-08-06	2027-12-01	Scrapped	Dr. Ashish Mishra	\N	1	CSE/20250728/GPU/Nvidia/Ashish/001	\N	\N	\N	\N
11	Dell 	Laptop	Dell	vostro	wer34	76y48	500000	CS-208	2025-10-01	2025-09-01	2025-09-11	Available	Prof. Antony Franklin	\N	1	CSE/20251001/Laptop/Dell/Antony/001	\N	\N	\N	\N
12	Dell 	Laptop	Dell	vostro	wer35	76y48	500000	CS-208	2025-10-01	2025-09-01	2025-09-11	Available	Prof. Antony Franklin	\N	1	CSE/20251001/Laptop/Dell/Antony/002	\N	\N	\N	\N
\.


--
-- Data for Name: equipment_history; Type: TABLE DATA; Schema: public; Owner: lab_user
--

COPY public.equipment_history (id, equipment_id, assigned_to_roll, assigned_by, assigned_date, unassigned_date, status_snapshot, "timestamp") FROM stdin;
1	4	cs23mtech12001	admin@cse.iith.ac.in	2025-08-30 14:46:13.100781	2025-09-01 06:49:46.574511	Returned	2025-08-30 14:46:13.106062
2	5	cs23mtech12001	admin@cse.iith.ac.in	2025-08-30 14:57:55.552342	2025-09-01 06:44:58.118926	Returned	2025-08-30 14:57:55.553507
3	7	cs25btech13001	admin@cse.iith.ac.in	2025-08-30 15:23:20.89484	2025-09-01 06:43:39.159347	Returned	2025-08-30 15:23:20.900741
4	6	cs25btech11001	admin@cse.iith.ac.in	2025-08-31 12:39:23.978774	\N	Issued	2025-08-31 12:39:23.993285
5	1	cs23mtech12001	admin@cse.iith.ac.in	2025-08-30 14:46:13.100781	2025-09-01 06:45:00.90367	Returned	2025-09-01 06:45:00.905545
6	2	cs23mtech12001	admin@cse.iith.ac.in	2025-08-30 14:46:13.100781	2025-09-01 06:45:02.978324	Returned	2025-09-01 06:45:02.978682
7	3	cs23mtech12001	admin@cse.iith.ac.in	2025-08-30 14:46:13.100781	2025-09-01 06:45:06.855658	Returned	2025-09-01 06:45:06.855954
8	3	cs23mtech12001	admin@cse.iith.ac.in	2025-09-01 06:45:50.504514	2025-09-01 06:49:49.55197	Returned	2025-09-01 06:45:50.506065
9	7	cs23mtech12001	admin@cse.iith.ac.in	2025-09-01 06:47:02.837106	\N	Issued	2025-09-01 06:47:02.837945
10	5	cs23mtech12001	admin@cse.iith.ac.in	2025-09-01 06:47:12.079126	2025-09-01 06:49:51.316773	Returned	2025-09-01 06:47:12.079921
11	3	cs25mtech12007	admin@cse.iith.ac.in	2025-09-01 11:37:57.68668	2025-09-01 11:38:02.950409	Returned	2025-09-01 11:37:57.694346
12	3	cs25mtech12007	admin@cse.iith.ac.in	2025-09-01 11:38:08.330336	2025-09-01 11:38:11.414142	Returned	2025-09-01 11:38:08.330858
13	1	cs23mtech12001	admin@cse.iith.ac.in	2025-09-01 15:05:01.039501	2025-09-02 01:15:41.702646	Returned	2025-09-01 15:05:01.045475
14	4	cs23mtech12001	admin@cse.iith.ac.in	2025-09-01 15:05:19.935969	2025-09-01 15:06:52.779385	Returned	2025-09-01 15:05:19.937773
15	3	cs24mtech12004	admin@cse.iith.ac.in	2025-09-01 15:09:28.120947	2025-09-01 15:19:49.493063	Returned	2025-09-01 15:09:28.122148
16	4	cs24mtech12004	admin@cse.iith.ac.in	2025-09-01 15:19:08.339109	2025-09-01 15:19:20.939599	Returned	2025-09-01 15:19:08.34176
17	2	cs24mtech12004	admin@cse.iith.ac.in	2025-09-01 15:38:56.083865	2025-09-01 15:39:16.045439	Returned	2025-09-01 15:38:56.085435
18	2	cs24mtech12004	admin@cse.iith.ac.in	2025-09-01 15:45:25.747634	2025-09-01 15:45:42.686476	Returned	2025-09-01 15:45:25.752837
19	2	cs24mtech12004	admin@cse.iith.ac.in	2025-09-01 15:47:17.952826	2025-09-01 15:50:10.74487	Returned	2025-09-01 15:47:17.954403
20	2	cs24mtech12004	admin@cse.iith.ac.in	2025-09-01 15:53:35.809184	\N	Issued	2025-09-01 15:53:35.813447
21	1	123444	admin@cse.iith.ac.in	2025-09-02 01:17:27.412956	2025-09-02 01:37:49.546079	Returned	2025-09-02 01:17:27.416862
22	3	123444	admin@cse.iith.ac.in	2025-09-02 01:18:02.168748	2025-09-02 01:18:44.233664	Returned	2025-09-02 01:18:02.170359
\.


--
-- Data for Name: provisioning_request; Type: TABLE DATA; Schema: public; Owner: lab_user
--

COPY public.provisioning_request (id, mac_address, ip_address, os_image, "timestamp") FROM stdin;
\.


--
-- Data for Name: room_lab; Type: TABLE DATA; Schema: public; Owner: lab_user
--

COPY public.room_lab (id, name, capacity, staff_incharge) FROM stdin;
1	CS-107	43	G Praveen Kumar
2	CS-108	21	G Praveen Kumar
3	CS-109	114	G Praveen Kumar
4	CS-207	30	M Shiva Reddy
5	CS-208	25	M Shiva Reddy
6	CS-209	142	M Shiva Reddy
7	CS-317	25	Sunitha M
8	CS-318	25	Sunitha M
9	CS-319	32	Sunitha M
10	CS-320	27	Sunitha M
11	CS-411	25	Mr Nikith Reddy
12	CS-412	33	Mr Nikith Reddy
\.


--
-- Data for Name: slurm_account; Type: TABLE DATA; Schema: public; Owner: lab_user
--

COPY public.slurm_account (id, roll, status) FROM stdin;
3	cs24mtech12004	active
4	cs23mtech12001	active
5	cs25btech11001	active
\.


--
-- Data for Name: student; Type: TABLE DATA; Schema: public; Owner: lab_user
--

COPY public.student (roll, name, course, year, joining_year, faculty, email, phone, user_id) FROM stdin;
cs25btech11001	Raj	B.Tech	I	2025	Prof. M. V. Panduranga Rao	cs25btech11001@iith.ac.in	+919059217339	7
cs25mtech11003	praveen kumar	B.Tech	I	2025	Dr. Praveen Tammana	cs25mtech11003@iith.ac.in	+919059217339	8
cs25phd11221	praveen kumar	Ph.D.	III	2025	Dr. Praveen Tammana	cs25phd11221@iith.ac.in	+919059217339	9
cs25mtech12001	praveen kumar	M.Tech TA	II	2025	Prof. C. Krishna Mohan	cs25mtech12001@iith.ac.in	+919059217339	10
cs25btech12001	rajesh	B.Tech	I	2025	Prof. Bheemarjuna Reddy Tamma	cs25btech12001@iith.ac.in	+919059217339	11
123444	praveen kumar	B.Tech	I	2019	Dr. Nitin Saurabh	123444@iith.ac.in	+919059217339	12
cs23mtech12001	praveen kumar	M.Tech TA	I	2023	Dr. Maria Francis	cs23mtech12001@iith.ac.in	+919059217339	13
cs25btech13001	Ruthvik	B.Tech	I	2025	Prof. Antony Franklin	cs25btech13001@iith.ac.in	+919059217339	14
cs24mtech12004	Rajiv	M.Tech TA	II	2024	Dr. Jyothi Vedurada	cs24mtech12004@iith.ac.in	+919059217339	15
cs25mtech12007	Jeevan	M.Tech TA	I	2025	Dr. Manish Singh	cs25mtech12007@iith.ac.in	+919059217339	16
cs25btech14001	Pavan kumar	B.Tech	II	2025	Dr. Jyothi Vedurada	cs25btech14001@iith.ac.in	+919059217339	17
cs25btech11000	Rajesh	B.Tech	I	2025	Dr. Nitin Saurabh	cs25btech11000@iith.ac.in	+919059217339	18
cs25btech15001	Ram	B.Tech	I	2025	Dr. Rakesh Venkat	cs25btech15001@iith.ac.in	+919059217339	19
cs25mtech12010	Karthik	M.Tech TA	I	2025	Dr. J. Saketha Nath	cs25mtech12010@iith.ac.in	+919059217339	20
cs25mtech11001	Praveen	M.Tech TA	I	2025	Prof. Antony Franklin	cs25mtech11001@iith.ac.in	+919059217339	21
cs25mtech11051	Anil	M.Tech TA	I	2025	Dr. J. Saketha Nath	cs25mtech11051@iith.ac.in	+919059217339	22
cs25phd11011	balu	Ph.D.	I	2025	Dr. Kotaro Kataoka	cs25phd11011@iith.ac.in	+919059217339	23
cs25btech11021	Ram	B.Tech	I	2025	Dr. Nitin Saurabh	cs25btech11021@iith.ac.in	+919059217339	25
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: lab_user
--

COPY public."user" (id, email, password, role, is_approved, reset_token, reset_token_expiry, registered_at, approved_at, is_active) FROM stdin;
1	admin@cse.iith.ac.in	scrypt:32768:8:1$AbDvbYn0eqFGPbsp$97244656fed94cbd66e034ea896115e18bd6ede02cef0f293e0ccca6fe9fc85cac921d7d6a812f43590f73341784b6c64b25ccd3b1799f39ad524f96bde68583	admin	t	\N	\N	2025-08-15 16:46:48.419041	2025-08-15 16:46:48.419038	t
2	g.praveenkumar@cse.iith.ac.in	scrypt:32768:8:1$8lQvzYmKxxTTbY0M$b99a207d1e86f59921e6cefbf8dc5ba57d340865599b03cb655dae3ce06d91b385fe7055f338f14553b653f5f9f2bc80ac54b971ea409f2954911b1392bd15c0	staff	t	\N	\N	2025-09-02 00:40:08.59558	2025-09-02 00:40:48.307948	t
3	cs23mtech10045@iith.ac.in	scrypt:32768:8:1$BXXrUFRMgTruuTzg$24cad9492021ce007e768e16e3410da1df673add34db45170aea6ca554e334fc64365d13592364a9e352f150462678cd525c8aebbe5d46b660c96042810242d3	student	t	\N	\N	2025-09-13 15:20:18.413899	2025-09-13 15:27:14.812474	t
4	naveen@cse.iith.ac.in	scrypt:32768:8:1$fvsZKWaHgsw1s3JR$872413d7cfae660f69a21f0d7a032f3b1481cddb4ce293948476dc8ab29d491894777f441b11e7a508880b8e2272bbc7bb05a38ca075e1d777c93b7ffe85f454	faculty	t	\N	\N	2025-09-13 15:24:15.022045	2025-09-13 15:27:19.72297	t
5	praveent@cse.iith.ac.in	scrypt:32768:8:1$Enc1eXK4U0BC2yyo$aaceff685f8a897538c6556da11ad66d0a10cd1c8c684a51793035cc4cf12341bfe7c40b91c9dfb2b6065e5395cd88d360ceff1a3a84c353a05fac56f28eab2c	faculty	t	\N	\N	2025-09-13 15:40:16.758923	2025-09-13 15:40:52.836535	t
6	admin2@cse.iith.ac.in	scrypt:32768:8:1$TQEOdUgdnrDmrFJU$399e2255ced4b68486f7395066d723e40633e95939ad0386dc9b8e451524871ee0687d9ede5dc5818d4cdef58112d485b521cc0f7f28fb3af011762f6ba89dc5	admin	t	\N	\N	2025-09-13 15:43:05.161594	2025-09-13 15:43:25.055399	t
7	cs25btech11001@iith.ac.in	scrypt:32768:8:1$QO4pzJp8NkgsD1vd$b08ab0b8a25a5dc6e9100766b2d391d14595e43de7da5c8fd218b1555bd4ab974cfd873bb3aae0ab3794dc09030723c4e70f5c186698d50c1d26ffc3c503ded3	student	t	\N	\N	2025-09-13 16:34:48.147711	2025-09-15 05:50:23.925589	t
8	cs25mtech11003@iith.ac.in	scrypt:32768:8:1$cGvGJSZq8FxvZgXx$92e9d2a2ff53aec7fdbcd770293f55bed15e1c60bc39f887b5464d0b73f8327d41e4ff9c96fdc66ce03518def057428620980209bc83e8a8e846fd2998a32c5a	student	t	\N	\N	2025-09-13 16:34:48.254038	2025-09-15 05:51:06.732662	t
9	cs25phd11221@iith.ac.in	scrypt:32768:8:1$am5RSqIzK3ylYHq3$3926a03f1692cb913eff86481ad9472e9a87c003d38a556260426ef85e0d30a8ee3dc31bec0fcc9da92929a94a6486890a25f9c53ce73dc9dfef2414018617cb	student	t	\N	\N	2025-09-13 16:34:48.364315	2025-09-15 05:51:38.454488	t
10	cs25mtech12001@iith.ac.in	scrypt:32768:8:1$aev9UouQ16kkQbn8$8bf0a11d9c8a0258ce70717dc2ee4f82e4ad29ac69ff03d4acdfb0df616c024143efc62bfe2bc94ad6cec0e5f166f570590478a03688ab23030bbae6fcbc560f	student	t	\N	\N	2025-09-13 16:34:48.4714	2025-09-15 05:52:21.401463	t
11	cs25btech12001@iith.ac.in	scrypt:32768:8:1$PGYavNUCXBKRSU72$4362df30118ae167538d7162efb8761f1d77c391d5e5dc21aaf6b27f9c36f3c23c3b2e696bb32e4d9e70b0d5d08974457da34bd648143ef872878b6f517280e8	student	t	\N	\N	2025-09-13 16:34:48.576526	2025-09-15 05:52:25.842092	t
12	123444@iith.ac.in	scrypt:32768:8:1$HLJZKpyJBM3TJ7U7$b0a39b6791dd5322ab08f93e70fd0eba40e72635a0014e2b438a4deabc7d504d35cd548d9365450568ea9a02ee2c4a47b0e959eccb9c96fd1f0907bc65e52551	student	t	\N	\N	2025-09-13 16:34:48.679385	2025-09-15 06:33:07.375549	t
13	cs23mtech12001@iith.ac.in	scrypt:32768:8:1$C05Ht40Ql5kCsDPk$af62a566872178dd0096c863325e96718ac6e10949d21f3301d70afdec5e1217cb498afe2bd4a85875fa55894187dbbf2adfffd26556da08f578b635201669d4	student	t	\N	\N	2025-09-13 16:34:48.785443	2025-09-15 06:33:10.685627	t
14	cs25btech13001@iith.ac.in	scrypt:32768:8:1$xxxs8E5YtnlD1sZi$19a66fdff7f6a668bf9c0a010ac9e0e3b76dcab4396430873cbe822e66407203762f3d2e0d6ca005ce93ca2fb38073a3cbb88d6bef10a0e43151f729515d58d4	student	t	\N	\N	2025-09-13 16:34:48.889647	2025-09-15 06:33:11.618081	t
15	cs24mtech12004@iith.ac.in	scrypt:32768:8:1$Lnv7dRnFkJGdZcO7$05ace79754ef1f5eff4c17ccb5ad884e0a14e18c6e0372438c96eb1331ebfa6683d2e319c386aa38e2badd26a8bf68cee69e9c61b303e8f296ae1cccc2c6587b	student	t	\N	\N	2025-09-13 16:34:48.995197	2025-09-15 06:33:15.650552	t
16	cs25mtech12007@iith.ac.in	scrypt:32768:8:1$evCNjqSOPC6I1r7U$0567195ef8d9a3470b5618e4e26bca80efd4e02036623ef1fd5bb468f18d0fb4bfb49fe0120388009edd9d438c52fb7b6c3a44ef92150b2654ecda4f10721917	student	t	\N	\N	2025-09-13 16:34:49.098305	2025-09-15 06:33:16.747437	t
17	cs25btech14001@iith.ac.in	scrypt:32768:8:1$wm01tkh7NDFqLAZJ$8e21124cdbe73ce6368725075456fc3b1f12e26ccd5aefab61d0a7190972063b089af10c4f835f5e5287d4c47f891bcbaf8c20710b8c8831e387374a7235900d	student	t	\N	\N	2025-09-13 16:34:49.200466	2025-09-15 06:33:17.702608	t
18	cs25btech11000@iith.ac.in	scrypt:32768:8:1$x2QU2JSxWB5TeefH$86e4d81d8bb9a1e175480d53b8d78f117e3245bac76fa3e5cc52541b3b9eeb18943c01ee4f77d66a4627c0a2a2a3ec92b949c76d2e79813052dded13f0486609	student	t	\N	\N	2025-09-13 16:34:49.303405	2025-09-15 06:33:18.630454	t
19	cs25btech15001@iith.ac.in	scrypt:32768:8:1$QQfwLMq38enbDpUj$9cc22d66a1662306546f9921b686f39fe7feacb9b65b4568d0c5108c0610e27b74b73cf183e2368920978d06d530d0d4b54f9fdc751e126cb6fa8c2dfde147ac	student	t	\N	\N	2025-09-13 16:34:49.408312	2025-09-15 06:33:19.38521	t
20	cs25mtech12010@iith.ac.in	scrypt:32768:8:1$iA5e5H5sKbGYXmEF$92d330aa2d067c1de5ba79acfe391670372b61e75523d83bdef80efd190b91d14995c52b3bd3a10b3ebf62faf3d4d4e2b757a35629132a336ae957747e2563e8	student	t	\N	\N	2025-09-13 16:34:49.512428	2025-09-15 06:33:23.229624	t
21	cs25mtech11001@iith.ac.in	scrypt:32768:8:1$w2ZB87ipzxTlTb0b$4de5b9a99fce373f261844915212f9e980382852ea295c5e6014c133c355ff732926e3fb89c90331187eee4324d94d519c56a0642a68c31a8599b207bd3603ba	student	t	\N	\N	2025-09-13 16:34:49.616859	2025-09-15 05:40:30.92499	t
22	cs25mtech11051@iith.ac.in	scrypt:32768:8:1$X5ISjaTYKZku9v2Q$aabde1f125346aaf83e3c1eb32363c270aac4b460285178ac8d848d5cd22219b0a1b3d2d7a1f8c9d443e514d6aab093ad2eaa08591b2c17ed352a0a5d10443ab	student	t	\N	\N	2025-09-13 16:34:49.719366	2025-09-15 05:50:32.11936	t
23	cs25phd11011@iith.ac.in	scrypt:32768:8:1$Fq84eG4B4KcerJNj$3c926383fc7fde99a787c5587003428548aea6031161c1a0446c43e77ac792c22adb18d0c7d8a417da2a8c6730686a87c0b6e3f3407d69895d5332e3572186f8	student	t	\N	\N	2025-09-13 16:41:14.100979	2025-09-13 16:42:31.035229	t
24	sunitha.m@cse.iith.ac.in	scrypt:32768:8:1$pmHl3JlY059Mmqk1$17bf583982ee65811ca6f03d47c3976ce86f5404e7df063bb47817ce2c6852ea044ba3cbcbefe205a0e76a3a6f1bfa9c91a3aa1b5efd74217a216566f021a94e	staff	t	\N	\N	2025-09-14 14:32:49.396182	2025-09-14 14:33:13.27546	t
25	cs25btech11021@iith.ac.in	scrypt:32768:8:1$RCEB5kBtVIhJ02b7$bab54706e91d32a8a4cc72e7c39a28f6f749b76dc550ab33b2f289a0a2d970d389fab3c9ea03f5c7bb447f7749b5360d328df27bc0d4bcffdfb375702255394b	student	t	\N	\N	2025-09-15 05:53:02.379725	2025-09-15 05:55:52.183936	t
\.


--
-- Data for Name: workstation_asset; Type: TABLE DATA; Schema: public; Owner: lab_user
--

COPY public.workstation_asset (id, manufacturer, "otherManufacturer", model, serial, os, "otherOs", processor, cores, ram, "otherRam", storage_type1, storage_capacity1, storage_type2, storage_capacity2, gpu, vram, keyboard_provided, keyboard_details, mouse_provided, mouse_details, monitor_provided, monitor_details, monitor_size, monitor_serial, mac_address, po_date, source_of_fund, status, location, indenter, department_code) FROM stdin;
1	Dell	No	Laptop	1w23e4	macOS	None	Intel Silver	2	128	\N	HDD	1024	SSD	256	No	0	no	None	no	None	no	None	23	12345	90:5a:08:13:b8:c4	2025-08-14	Project	Available	CS-107	Dr. Nitin Saurabh	CSE/20250814/Dell/Laptop/Nitin/001
2	HP	No	Laptop	1w23e4t	macOS	None	Intel Silver	2	128	\N	HDD	1024	SSD	256	No	0	no	None	no	None	no	None	23	12345	90:5a:08:13:b8:c4	2025-08-14	Project	Available	CS-411	Dr. Manish Singh	CSE/20250814/HP/Laptop/Manish/002
3	Supermicro	No	Server	12ser433333	macOS	None	Intel i5	2	128	\N	HDD	1024	SSD	256	No	0	no	None	no	None	no	None	\N	None	90:5b:08:13:b8:c4	2025-08-28	Project	Available	CS-320	Prof. M.V.Panduranga Rao	CSE/20250828/Supermicro/Server/MVP/003
4	Lenovo	\N	Laptop	2190x456	Ubuntu	\N	Intel i7	32	64	\N	SSD	512	HDD	1025	NO	0	yes	Dell	yes	Dell	yes	Dell	24	12345fgtr	12:AA:VV:CF:1E:31	2025-09-15	Project	Available	CS-107	Dr. Jyothi Vedurada	CSE/20250915/Lenovo/Laptop/Jyothi/004
5	ASUS	\N	2345	1w23e4t111	Ubuntu	\N	Intel Gold	32	128	\N	SSD	512	SSD	256	NO	0	no	\N	no	\N	no	\N	\N	\N	12:AA:VV:CF:1E:66	2025-09-02	Project	Available	CS-208	Dr. Jyothi Vedurada	CSE/20250902/ASUS/2345/Jyothi/005
6	Fujitsu	\N	Axo2	12ser432w	Windows	\N	Intel i7	12	4	\N	NVMe	512	HDD	1024	NO	0	no	\N	no	\N	no	\N	\N	\N	12:AA:VV:CF:1E:13	2025-09-01	Project	Available	CS-317	Dr. Rajesh Kedia	CSE/20250901/Fujitsu/Axo2/Rajesh/006
7	Dell	\N	Laptop Vostro	123	Windows	\N	INTEL(R) XEON(R) GOLD 6526Y	32	32	\N	NVMe	256	SSD	\N	No	0	no	\N	no	\N	laptop	\N	\N	\N	12:AA:VV:CF:1E:45	2025-09-17	Project	Available	CS-207	Dr. Maria Francis	CSE/20250917/Dell/Laptop Vostro/Maria/007
8	Apple	\N	Mac	12we34	macOS	\N	intel	24	64	\N	NVMe	256	\N	\N	No	0	no	\N	no	\N	no	\N	\N	\N	12:AA:VV:CF:1E:23	2025-09-18	Institute	Available	CS-107	Prof. Antony Franklin	CSE/20250918/Apple/Mac/Antony/008
\.


--
-- Data for Name: workstation_assignment; Type: TABLE DATA; Schema: public; Owner: lab_user
--

COPY public.workstation_assignment (id, workstation_id, student_roll, issue_date, system_required_till, end_date, remarks, is_active) FROM stdin;
1	3	cs25btech11001	2025-08-23	2025-08-31	2025-08-16	\N	f
2	2	cs25btech11001	2025-08-14	2025-08-30	2025-08-16	\N	f
3	2	cs25btech11001	2025-08-22	2025-08-31	2025-08-16	\N	f
4	3	cs25phd11221	2025-08-17	2025-08-23	2025-08-18	\N	f
5	2	cs25phd11221	2025-08-23	2025-08-24	2025-08-16	\N	f
6	1	cs25btech11001	2025-08-16	2025-08-30	2025-08-16	\N	f
7	2	cs25btech11001	2025-08-17	2025-08-24	2025-08-18	\N	f
8	1	cs25mtech12001	2025-12-21	2026-12-21	2025-08-18	\N	f
9	3	cs23mtech12001	2025-08-12	2025-08-19	2025-08-18	\N	f
10	2	cs25mtech12001	2025-08-19	2025-08-24	2025-09-15	\N	f
11	1	cs23mtech12001	2025-08-20	2025-08-23	2025-08-18	\N	f
12	3	cs23mtech12001	2025-08-18	2025-08-20	2025-08-31	\N	f
13	1	cs25btech15001	2025-08-21	2025-08-30	2025-09-15	\N	f
14	5	cs23mtech12001	2025-09-01	2025-09-24	2025-09-02	\N	f
15	3	cs24mtech12004	2025-09-09	2025-10-12	2025-09-01	\N	f
16	6	cs24mtech12004	2025-09-09	2025-09-19	2025-09-14	\N	f
17	5	cs23mtech12001	2025-09-10	2025-09-20	2025-09-14	\N	f
\.


--
-- Name: cubicle_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lab_user
--

SELECT pg_catalog.setval('public.cubicle_id_seq', 1, false);


--
-- Name: equipment_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lab_user
--

SELECT pg_catalog.setval('public.equipment_history_id_seq', 1, false);


--
-- Name: equipment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lab_user
--

SELECT pg_catalog.setval('public.equipment_id_seq', 1, false);


--
-- Name: provisioning_request_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lab_user
--

SELECT pg_catalog.setval('public.provisioning_request_id_seq', 1, false);


--
-- Name: room_lab_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lab_user
--

SELECT pg_catalog.setval('public.room_lab_id_seq', 1, false);


--
-- Name: slurm_account_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lab_user
--

SELECT pg_catalog.setval('public.slurm_account_id_seq', 1, false);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lab_user
--

SELECT pg_catalog.setval('public.user_id_seq', 1, false);


--
-- Name: workstation_asset_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lab_user
--

SELECT pg_catalog.setval('public.workstation_asset_id_seq', 1, false);


--
-- Name: workstation_assignment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lab_user
--

SELECT pg_catalog.setval('public.workstation_assignment_id_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: cubicle cubicle_pkey; Type: CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.cubicle
    ADD CONSTRAINT cubicle_pkey PRIMARY KEY (id);


--
-- Name: equipment equipment_department_code_key; Type: CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.equipment
    ADD CONSTRAINT equipment_department_code_key UNIQUE (department_code);


--
-- Name: equipment_history equipment_history_pkey; Type: CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.equipment_history
    ADD CONSTRAINT equipment_history_pkey PRIMARY KEY (id);


--
-- Name: equipment equipment_pkey; Type: CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.equipment
    ADD CONSTRAINT equipment_pkey PRIMARY KEY (id);


--
-- Name: provisioning_request provisioning_request_pkey; Type: CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.provisioning_request
    ADD CONSTRAINT provisioning_request_pkey PRIMARY KEY (id);


--
-- Name: room_lab room_lab_pkey; Type: CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.room_lab
    ADD CONSTRAINT room_lab_pkey PRIMARY KEY (id);


--
-- Name: slurm_account slurm_account_pkey; Type: CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.slurm_account
    ADD CONSTRAINT slurm_account_pkey PRIMARY KEY (id);


--
-- Name: slurm_account slurm_account_roll_key; Type: CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.slurm_account
    ADD CONSTRAINT slurm_account_roll_key UNIQUE (roll);


--
-- Name: student student_email_key; Type: CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.student
    ADD CONSTRAINT student_email_key UNIQUE (email);


--
-- Name: student student_pkey; Type: CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.student
    ADD CONSTRAINT student_pkey PRIMARY KEY (roll);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: workstation_asset workstation_asset_pkey; Type: CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.workstation_asset
    ADD CONSTRAINT workstation_asset_pkey PRIMARY KEY (id);


--
-- Name: workstation_assignment workstation_assignment_pkey; Type: CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.workstation_assignment
    ADD CONSTRAINT workstation_assignment_pkey PRIMARY KEY (id);


--
-- Name: ix_cubicle_student_roll; Type: INDEX; Schema: public; Owner: lab_user
--

CREATE INDEX ix_cubicle_student_roll ON public.cubicle USING btree (student_roll);


--
-- Name: ix_equipment_assigned_to_roll; Type: INDEX; Schema: public; Owner: lab_user
--

CREATE INDEX ix_equipment_assigned_to_roll ON public.equipment USING btree (assigned_to_roll);


--
-- Name: ix_equipment_history_assigned_to_roll; Type: INDEX; Schema: public; Owner: lab_user
--

CREATE INDEX ix_equipment_history_assigned_to_roll ON public.equipment_history USING btree (assigned_to_roll);


--
-- Name: ix_equipment_history_equipment_id; Type: INDEX; Schema: public; Owner: lab_user
--

CREATE INDEX ix_equipment_history_equipment_id ON public.equipment_history USING btree (equipment_id);


--
-- Name: ix_equipment_serial_number; Type: INDEX; Schema: public; Owner: lab_user
--

CREATE UNIQUE INDEX ix_equipment_serial_number ON public.equipment USING btree (serial_number);


--
-- Name: ix_provisioning_request_mac_address; Type: INDEX; Schema: public; Owner: lab_user
--

CREATE INDEX ix_provisioning_request_mac_address ON public.provisioning_request USING btree (mac_address);


--
-- Name: ix_room_lab_name; Type: INDEX; Schema: public; Owner: lab_user
--

CREATE UNIQUE INDEX ix_room_lab_name ON public.room_lab USING btree (name);


--
-- Name: ix_user_email; Type: INDEX; Schema: public; Owner: lab_user
--

CREATE UNIQUE INDEX ix_user_email ON public."user" USING btree (email);


--
-- Name: ix_workstation_asset_department_code; Type: INDEX; Schema: public; Owner: lab_user
--

CREATE UNIQUE INDEX ix_workstation_asset_department_code ON public.workstation_asset USING btree (department_code);


--
-- Name: ix_workstation_asset_serial; Type: INDEX; Schema: public; Owner: lab_user
--

CREATE UNIQUE INDEX ix_workstation_asset_serial ON public.workstation_asset USING btree (serial);


--
-- Name: ix_workstation_asset_status; Type: INDEX; Schema: public; Owner: lab_user
--

CREATE INDEX ix_workstation_asset_status ON public.workstation_asset USING btree (status);


--
-- Name: ix_workstation_assignment_is_active; Type: INDEX; Schema: public; Owner: lab_user
--

CREATE INDEX ix_workstation_assignment_is_active ON public.workstation_assignment USING btree (is_active);


--
-- Name: ix_workstation_assignment_student_roll; Type: INDEX; Schema: public; Owner: lab_user
--

CREATE INDEX ix_workstation_assignment_student_roll ON public.workstation_assignment USING btree (student_roll);


--
-- Name: ix_workstation_assignment_workstation_id; Type: INDEX; Schema: public; Owner: lab_user
--

CREATE INDEX ix_workstation_assignment_workstation_id ON public.workstation_assignment USING btree (workstation_id);


--
-- Name: cubicle cubicle_room_lab_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.cubicle
    ADD CONSTRAINT cubicle_room_lab_id_fkey FOREIGN KEY (room_lab_id) REFERENCES public.room_lab(id);


--
-- Name: cubicle cubicle_student_roll_fkey; Type: FK CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.cubicle
    ADD CONSTRAINT cubicle_student_roll_fkey FOREIGN KEY (student_roll) REFERENCES public.student(roll);


--
-- Name: equipment fk_equipment_assigned_to_roll; Type: FK CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.equipment
    ADD CONSTRAINT fk_equipment_assigned_to_roll FOREIGN KEY (assigned_to_roll) REFERENCES public.student(roll);


--
-- Name: equipment_history fk_equipment_history_assigned_to_roll; Type: FK CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.equipment_history
    ADD CONSTRAINT fk_equipment_history_assigned_to_roll FOREIGN KEY (assigned_to_roll) REFERENCES public.student(roll);


--
-- Name: slurm_account slurm_account_roll_fkey; Type: FK CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.slurm_account
    ADD CONSTRAINT slurm_account_roll_fkey FOREIGN KEY (roll) REFERENCES public.student(roll);


--
-- Name: student student_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.student
    ADD CONSTRAINT student_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: workstation_assignment workstation_assignment_student_roll_fkey; Type: FK CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.workstation_assignment
    ADD CONSTRAINT workstation_assignment_student_roll_fkey FOREIGN KEY (student_roll) REFERENCES public.student(roll);


--
-- Name: workstation_assignment workstation_assignment_workstation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: lab_user
--

ALTER TABLE ONLY public.workstation_assignment
    ADD CONSTRAINT workstation_assignment_workstation_id_fkey FOREIGN KEY (workstation_id) REFERENCES public.workstation_asset(id);


--
-- PostgreSQL database dump complete
--

