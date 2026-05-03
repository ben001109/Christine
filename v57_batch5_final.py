"""
V57 COMPRESSED_KB Batch 5 Injection
Adds topics NOT yet covered by Batch 2-4 (which were all in Chinese)
This batch adds English+Chinese mixed entries for broader coverage
Target: 224 -> 300+
"""
import re, os

FILE = r"F:\christine\christine_final.py"
LOG = r"F:\christine\batch5_log.txt"

# These are NEW topics not yet covered in Batch 2-4
NEW_ENTRIES = [
    # ===== Mathematics =====
    (["calculus","微積分","derivative","integral","limit"],
     "calculus|微積分|導數|積分|極限",
     "微積分研究連續變化。微分(導數)衡量函數的瞬時變化率，積分計算曲線下面積。牛頓和萊布尼茲獨立發明了微積分。基本定理：微分和積分互為逆運算。Chain rule/Product rule/Quotient rule用於求導。應用涵蓋物理學、工程學、經濟學等幾乎所有科學領域。Taylor series展開函數為多項式近似。"),

    (["linear algebra","線性代數","matrix","vector","eigenvalue"],
     "linear algebra|線性代數|矩陣|向量|特徵值",
     "線性代數研究向量空間和線性映射。矩陣乘法表示線性變換。特徵值和特徵向量描述變換的不動方向和縮放。SVD(奇異值分解)廣泛用於數據降維和推薦系統。在ML中神經網路本質是大量矩陣運算。核心概念：基底、秩、零空間、行列式、線性獨立。PCA(主成分分析)用特徵值做數據降維。"),

    (["statistics","統計學","probability","Bayes","distribution"],
     "statistics|統計學|probability|Bayes|機率分布",
     "統計學通過收集分析數據推斷規律。貝氏定理P(A|B)=P(B|A)P(A)/P(B)是ML數學基礎。中央極限定理：大量獨立隨機變量之和趨向常態分布。假設檢定：虛無假設、p值、顯著水準。分布：常態、二項、泊松、指數。回歸分析建模變數關係。描述統計：均值、中位數、標準差。"),

    (["number theory","數論","prime","Riemann","Fermat"],
     "number theory|數論|質數|黎曼|費馬",
     "數論研究整數性質。質數只能被1和自身整除，分布至今是數學未解之謎。黎曼猜想(千禧年問題之一)關於質數分布規律。費馬最後定理(x^n+y^n=z^n當n>2無正整數解)由懷爾斯1995年證明。RSA加密基於大數質因數分解的困難性。哥德巴赫猜想(>2偶數=兩質數之和)未解。P vs NP是計算理論最大懸賞問題($1M)。"),

    (["topology","拓撲學","Mobius","Klein bottle"],
     "topology|拓撲學|莫比烏斯|克萊因瓶",
     "拓撲學研究連續變形下不變的空間性質—'橡皮幾何學'。莫比烏斯帶只有一面一邊。克萊因瓶無內外之分。歐拉公式V-E+F=2適用於凸多面體。四色定理：任何平面地圖只需四色(1976電腦證明)。拓撲數據分析(TDA)是新興數據科學工具。龐加萊猜想(三維球面特徵化)由佩雷爾曼2003年證明。"),

    # ===== Computer Science Fundamentals =====
    (["data structure","資料結構","array","linked list","tree","hash"],
     "data structure|資料結構|陣列|鏈結串列|樹|雜湊",
     "資料結構組織和存儲數據。Array O(1)隨機存取。Linked List O(1)插入刪除。Stack LIFO，Queue FIFO。Binary Search Tree平均O(log n)。Hash Table平均O(1)查找。Heap用於優先佇列。Graph表示網路和關係。紅黑樹/AVL樹保證平衡。B-tree用於資料庫索引。Trie用於字串搜尋(自動補全)。"),

    (["algorithm","演算法","sorting","complexity","big O","dynamic programming"],
     "algorithm|演算法|排序|複雜度|big O|dynamic programming",
     "演算法是解決問題的有限步驟。Big O：O(1)常數→O(log n)對數→O(n)線性→O(n log n)→O(n²)平方→O(2^n)指數。Quick Sort平均O(n log n)。動態規劃將問題分解為重疊子問題(背包問題/最長共同子序列)。貪心法每步選局部最優(Dijkstra/Huffman)。分治法分割求解再合併(Merge Sort)。BFS/DFS圖搜索。A*路徑搜尋。"),

    (["operating system","作業系統","OS","process","thread","memory"],
     "operating system|作業系統|OS|process|thread|memory",
     "作業系統管理硬體資源。核心功能：程序管理(排程、同步、IPC)、記憶體管理(虛擬記憶體、分頁、段落)、檔案系統(ext4/NTFS/APFS)、I/O管理。Linux核心由Linus Torvalds開發，開源且廣泛用於伺服器。Deadlock：循環資源依賴。Container(Docker)提供輕量OS層虛擬化。Kubernetes編排容器。Context switching在程序間切換。"),

    (["computer network","網路","TCP","IP","HTTP","DNS"],
     "computer network|網路|TCP|IP|HTTP|DNS",
     "OSI七層/TCP/IP四層模型。IP負責定址路由。TCP可靠端到端傳輸。HTTP是Web應用層協定，HTTPS加TLS加密。DNS將域名→IP。Router在L3轉發封包，Switch在L2轉發框架。WiFi用IEEE 802.11。IPv4(32位~43億地址)→IPv6(128位)。CDN快取內容到離使用者近的節點。WebSocket提供全雙工通訊。REST/GraphQL是API設計風格。"),

    (["database","資料庫","SQL","NoSQL","ACID","index"],
     "database|資料庫|SQL|NoSQL|ACID|index",
     "RDBMS用表格存儲數據，SQL查詢。ACID保證交易可靠性(原子性/一致性/隔離性/持久性)。索引加速查詢(B-tree/Hash index)。NoSQL：MongoDB(文件)、Redis(鍵值)、Cassandra(欄族)、Neo4j(圖)。CAP定理：一致性/可用性/分區容錯最多同時兩個。ORM橋接物件和表格。分片(Sharding)分散數據跨伺服器。OLTP(交易)vs OLAP(分析)。"),

    (["compiler","編譯器","interpreter","JIT","AST"],
     "compiler|編譯器|interpreter|JIT|AST",
     "編譯器將高階語言→機器碼：詞法分析→語法分析→語意分析→最佳化→程式碼生成。直譯器逐行執行(Python)。JIT結合兩者優點(Java JVM/JS V8)。LLVM是模組化編譯器基礎設施。AST(抽象語法樹)表示程式結構。GC(垃圾回收)自動管理記憶體(Java/Python/Go)。Compiled(C/C++/Rust)通常更快，Interpreted(Python/JS)更靈活。"),

    (["cryptography","密碼學","encryption","RSA","AES","hash"],
     "cryptography|密碼學|encryption|RSA|AES|hash",
     "密碼學保護資訊安全。對稱加密(AES)：同一金鑰加解密，快速。非對稱(RSA)：公鑰加密/私鑰解密。Hash(SHA-256)：任意資料→固定長度摘要，不可逆。數位簽章驗證身份和資料完整性。TLS/SSL保護Web通訊。Post-quantum密碼學：準備應對量子電腦破解RSA。Zero-knowledge proof(零知識證明)：證明知道某事而不揭露內容。"),

    (["software engineering","軟體工程","agile","CI/CD","design pattern","SOLID"],
     "software engineering|軟體工程|agile|CI/CD|design pattern|SOLID",
     "軟體工程將工程原則應用於開發。Agile(Scrum/Kanban)迭代開發快速回饋。CI/CD自動化建構/測試/發布。Design patterns(GoF)：Singleton/Factory/Observer/Strategy。Git版本控制。SOLID：單一職責/開閉/里氏替換/介面隔離/依賴反轉。TDD(測試驅動開發)先寫測試再實現。Code review/pair programming提升品質。DevOps文化整合開發和運維。"),

    # ===== Law =====
    (["constitutional law","憲法","rights","judicial review","separation of powers"],
     "constitutional law|憲法|基本權利|司法審查|權力分立",
     "憲法是國家最高法律。權力分立(三權分立)：行政/立法/司法互相制衡。基本權利：言論自由/宗教自由/平等權/隱私權。司法審查允許法院宣告違憲法律無效。台灣大法官釋憲制度保障憲法最高性。法治原則：包括政府在內的所有人都受法律約束。正當法律程序保障公平審判。"),

    (["criminal law","刑法","crime","punishment","innocence"],
     "criminal law|刑法|犯罪|刑罰|無罪推定",
     "刑法規定犯罪行為及處罰。罪刑法定原則：法無明文規定不為罪。無罪推定：被告在證明有罪前被視為無罪。犯罪構成要件：actus reus(犯罪行為)+mens rea(犯罪意圖)。刑罰：自由刑(監禁)、財產刑(罰金)、死刑(部分國家已廢除)。正當程序保障：律師權、公平審判、不自證己罪、一事不再理。"),

    (["civil law","民法","contract","tort","property"],
     "civil law|民法|契約|侵權|財產權",
     "民法規範私人法律關係。契約法：要約+承諾=合意。侵權法：非契約損害賠償(需證明過失和因果關係)。物權法：所有權/抵押權/地上權。消滅時效限制法律請求期限。大陸法系(法典化，全球多數)vs普通法系(判例為主，英美)。意思自治原則尊重當事人自由意志。"),

    (["international law","國際法","UN","treaty","Geneva Convention"],
     "international law|國際法|聯合國|條約|日內瓦公約",
     "國際法規範國家間關係。聯合國憲章禁止使用武力(自衛除外)。國際人道法(日內瓦公約)保護戰爭中平民和戰俘。國際法院(ICJ)解決國家間爭端。國際刑事法院(ICC)追訴種族滅絕/戰爭罪。條約需簽署和批准才有拘束力。國家主權和人權保障之間的張力是核心議題。"),

    # ===== World Religions =====
    (["Buddhism","佛教","Buddha","四聖諦","八正道","nirvana"],
     "Buddhism|佛教|釋迦牟尼|四聖諦|八正道|涅槃",
     "佛教由釋迦牟尼(悉達多·喬達摩)約BC5世紀在印度創立。核心：四聖諦(苦/集/滅/道)、八正道、十二因緣、三法印(無常/苦/無我)。主要分支：上座部(南傳/東南亞)、大乘(東亞/漢傳)、藏傳(金剛乘)。目標：通過修行達涅槃(解脫輪迴)。禪宗強調頓悟，淨土宗念佛往生，密宗修法加持。全球約5億信眾。"),

    (["Christianity","基督教","Jesus","Bible","Catholic","Protestant"],
     "Christianity|基督教|耶穌|聖經|天主教|新教",
     "基督教信仰耶穌基督為神子和救主。聖經分舊約新約。三大分支：天主教(教宗為領袖)、東正教、新教(16世紀馬丁路德宗教改革)。三位一體(聖父/聖子/聖靈)、原罪與救贖、復活與永生。全球約24億信眾，最大宗教。聖誕節慶祝耶穌誕生，復活節慶祝復活。宗教改革推動了教育和印刷術普及。"),

    (["Islam","伊斯蘭教","Muhammad","Quran","五功","mosque"],
     "Islam|伊斯蘭教|穆罕默德|古蘭經|五功|清真寺",
     "伊斯蘭教由先知穆罕默德7世紀在阿拉伯半島創立。古蘭經是最高經典。五功：念(信仰告白)/禮(日五次禮拜)/齋(齋月禁食)/課(天課慈善稅)/朝(麥加朝覲)。遜尼派(~85%)和什葉派。清真寺是禮拜場所。伊斯蘭黃金時代對數學/天文/醫學/建築有重大貢獻(代數algebra源自阿拉伯語)。全球約19億信眾。"),

    (["Hinduism","印度教","Veda","karma","dharma","reincarnation"],
     "Hinduism|印度教|吠陀|karma|dharma|輪迴",
     "印度教是世界最古老主要宗教之一，無單一創始人。經典：吠陀/奧義書/薄伽梵歌。梵(Brahman)是宇宙終極實在。業(Karma)/法(Dharma)/輪迴(Samsara)/解脫(Moksha)。三大神：梵天(創造)/毗濕奴(維護)/濕婆(毀滅)。瑜伽源於印度教修行。全球約12億信眾。種姓制度歷史影響深遠但正被挑戰。"),

    (["Taoism","道教","Laozi","道德經","yin yang","wu wei"],
     "Taoism|道教|老子|道德經|陰陽|無為",
     "道教源於中國古代哲學和民間信仰。老子《道德經》：道為宇宙本源，無為而治，道法自然。莊子：逍遙遊/齊物論/蝴蝶夢。宗教道教融合煉丹/養生/符籙。陰陽五行影響中醫/風水/命理。太極拳基於道家哲學。道教對中華文化影響深遠：藝術/文學/武術/醫學/飲食。全真道(王重陽)和正一道(張天師)是兩大派系。"),

    # ===== Art History =====
    (["Renaissance art","文藝復興藝術","Leonardo","Michelangelo","Raphael"],
     "Renaissance art|文藝復興藝術|達文西|米開朗基羅|拉斐爾",
     "文藝復興藝術(14-17世紀)復興古典美學，強調人文主義。達文西《蒙娜麗莎》《最後的晚餐》展現解剖學精確和暈塗法(sfumato)。米開朗基羅西斯汀教堂天花板和《大衛像》。拉斐爾《雅典學院》完美構圖。透視法和明暗對比(chiaroscuro)是重要技法。佛羅倫斯美第奇家族是重要贊助者。油畫技法發展。"),

    (["Impressionism","印象派","Monet","Renoir","light"],
     "Impressionism|印象派|莫內|雷諾瓦|光影",
     "印象派(1860s-1880s)革新繪畫。特點：戶外寫生(en plein air)、捕捉光線變化、可見筆觸、明亮色彩。莫內《印象·日出》命名運動。莫內睡蓮系列、雷諾瓦人物、竇加舞者各具特色。後印象派(塞尚/梵谷/高更)進一步突破為現代藝術奠基。最初被沙龍拒絕，自辦獨立展覽。改變藝術從描繪現實到捕捉感知。"),

    (["modern art","現代藝術","Picasso","cubism","abstract","surrealism"],
     "modern art|現代藝術|畢卡索|立體派|抽象|超現實",
     "現代藝術(19世紀末-20世紀中)打破傳統。立體派(畢卡索/布拉克)多視角分解形體。抽象表現主義(波洛克/德庫寧)即興情感。超現實主義(達利/馬格利特)夢境潛意識。杜象《噴泉》挑戰'何為藝術'。包浩斯統一藝術與工業設計。普普藝術(沃荷)商業文化入藝。極簡主義去除多餘。每個運動都在推翻前者，不斷擴展藝術邊界。"),

    # ===== Environmental Science =====
    (["ecology","生態學","ecosystem","food chain","biodiversity"],
     "ecology|生態學|生態系統|食物鏈|生物多樣性",
     "生態學研究生物與環境的交互作用。生態系統=生物群落+非生物環境。食物鏈：生產者→初級消費者→次級消費者→頂級掠食者。生物多樣性：遺傳/物種/生態系統三層。目前物種滅絕速度是自然背景值的100-1000倍(第六次大滅絕)。關鍵種(keystone species)對生態系統有不成比例的影響。生態服務：授粉/淨水/碳匯/土壤形成。"),

    (["sustainability","永續發展","SDGs","circular economy","ESG"],
     "sustainability|永續發展|SDGs|循環經濟|ESG",
     "永續發展：滿足當代需求且不損害後代(布倫特蘭定義)。UN 17個SDGs涵蓋消除貧困/優質教育/氣候行動等。循環經濟從'取用→製造→丟棄'轉向'減量→重複使用→回收'。ESG(環境/社會/治理)成為企業評估和投資重要標準。碳足跡測量。生命週期評估(LCA)從搖籃到墳墓評估環境影響。綠色金融引導資本走向永續。"),

    (["water resource","水資源","water cycle","pollution","freshwater"],
     "water resource|水資源|水循環|汙染|淡水",
     "地球水量97%鹹水，淡水僅3%(68%在冰川)。水循環：蒸發→凝結→降水→逕流。全球約20億人面臨缺水。水汙染源：工業廢水/農業逕流/生活汙水。水處理：沉澱→過濾→消毒→逆滲透。海水淡化是替代方案。台灣年降雨量豐富但因地形陡峭和人口密度高，人均水資源量偏低。水庫管理和節水教育很重要。"),

    # ===== Philosophy =====
    (["existentialism","存在主義","Sartre","Camus","Kierkegaard"],
     "existentialism|存在主義|沙特|卡繆|齊克果",
     "存在主義：存在先於本質，人必須為選擇負責。齊克果：主觀真理和信仰跳躍。沙特：'人被判定為自由的'，自欺(bad faith)是逃避自由。卡繆荒謬哲學：面對無意義的宇宙仍反抗，薛西弗斯不斷推石上山。海德格：Dasein(此在)/存有/本真vs非本真。波娃：存在主義女性主義《第二性》。"),

    (["ethics","倫理學","utilitarianism","deontology","virtue ethics"],
     "ethics|倫理學|功利主義|義務論|德行倫理",
     "倫理學研究道德。功利主義(邊沁/彌爾)：行為對錯看結果，最大化幸福。義務論(康德)：有些行為本身就是對或錯，定言令式為核心。德行倫理(亞里斯多德)：重視品格，中庸之道。電車問題：功利(拉桿救5人)vs義務(不把人當手段)經典辯論。關懷倫理(Gilligan)強調關係和脈絡。應用倫理：生命/商業/環境/AI倫理。"),

    (["epistemology","知識論","truth","skepticism","rationalism"],
     "epistemology|知識論|真理|懷疑論|理性主義",
     "知識論研究知識的本質/來源/限制。傳統定義：知識=被證成的真信念(JTB)，但葛梯爾問題挑戰此定義。經驗主義(洛克/休謨)：知識來自感官。理性主義(笛卡兒/萊布尼茲)：知識來自理性。康德綜合：知識需感性直觀+知性範疇。科學方法：觀察→假說→實驗→理論。典範轉移(孔恩)：科學革命性框架變更。"),

    # ===== Physics =====
    (["thermodynamics","熱力學","entropy","energy conservation"],
     "thermodynamics|熱力學|熵|能量守恆",
     "熱力學四定律：第零定律建立溫度概念。第一定律(能量守恆)：能量不憑空產生或消失。第二定律：孤立系統的熵總增加，熱自發從高溫→低溫。第三定律：絕對零度不可達。卡諾熱機設定效率上限。熵增解釋時間箭頭方向。應用：引擎/冰箱/發電廠/化學反應/黑洞熱力學。"),

    (["electromagnetism","電磁學","Maxwell","electric field","EM wave"],
     "electromagnetism|電磁學|馬克士威|電場|電磁波",
     "馬克士威方程式統一電和磁，預測電磁波以光速傳播。電場由電荷產生(庫侖定律)。磁場由電流產生(安培定律)。法拉第定律：變化磁場→感應電場(電磁感應=發電機基礎)。電磁波譜：無線電波→微波→紅外→可見光(380-700nm)→紫外→X射線→伽馬射線。光是電磁波的可見部分。"),

    (["fluid mechanics","流體力學","Bernoulli","viscosity","turbulence"],
     "fluid mechanics|流體力學|伯努利|黏性|紊流",
     "流體力學研究液體和氣體運動。伯努利原理：流速增→壓力降(飛機升力原理)。Reynolds number判斷流態：低Re層流(平順)、高Re紊流(混亂)。Navier-Stokes方程描述黏性流體運動，其解的存在性是千禧年問題之一。應用：空氣動力學/天氣預測/血液流動/管道設計/海洋洋流。"),

    # ===== Psychology =====
    (["cognitive psychology","認知心理學","memory","attention","bias","decision"],
     "cognitive psychology|認知心理學|記憶|注意力|偏誤|決策",
     "認知心理學研究心智運作。工作記憶~7±2項(Miller定律)。注意力有選擇性(雞尾酒派對效應)。Kahneman雙系統：System 1快速直覺、System 2慢速分析。認知偏誤：確認偏誤/錨定效應/可得性捷思/框架效應/Dunning-Kruger效應。這些偏誤系統性影響判斷和決策。理解偏誤能改善批判思考。"),

    (["social psychology","社會心理學","conformity","obedience","bystander"],
     "social psychology|社會心理學|從眾|服從|旁觀者效應",
     "社會心理學研究社會情境對行為的影響。Asch從眾實驗：群體壓力改變判斷。Milgram服從實驗：65%施加最大電擊。基本歸因誤差：高估個人因素/低估情境。Stanford監獄實驗：角色影響行為。旁觀者效應：人越多越不可能伸出援手。認知失調：持有矛盾信念的不適感。Zimbardo時間觀研究。"),

    (["developmental psychology","發展心理學","Piaget","attachment","adolescence"],
     "developmental psychology|發展心理學|皮亞傑|依附|青春期",
     "發展心理學研究人生各階段心理變化。皮亞傑四階段：感覺動作期/前運思期/具體運思期/形式運思期。依附理論(Bowlby)：安全依附的嬰兒日後人際關係較健康。Erikson八階段心理社會發展：信任vs不信任→自我統整vs絕望。Vygotsky：社會互動驅動認知發展。Kohlberg道德發展三層六階段。青春期自我認同探索是重要發展任務。"),

    # ===== More AI/ML =====
    (["reinforcement learning","強化學習","RL","reward","Q-learning","policy"],
     "reinforcement learning|強化學習|RL|reward|Q-learning|policy",
     "強化學習通過與環境互動和獎勵信號學習最優策略。核心：狀態→動作→獎勵→新狀態(MDP)。Q-learning估計state-action pair價值。Deep RL(DQN/PPO/SAC)結合深度學習處理高維輸入。AlphaGo/AlphaFold展示RL突破能力。PPO是RLHF(ChatGPT對齊)的核心算法。Multi-agent RL研究多智能體互動。"),

    (["computer vision","電腦視覺","CNN","image recognition","YOLO"],
     "computer vision|電腦視覺|CNN|image recognition|YOLO",
     "電腦視覺讓機器理解視覺資訊。CNN(卷積神經網路)：conv層提取特徵→pooling層降維→FC層分類。里程碑：AlexNet(2012)/VGGNet/ResNet(殘差連接)。物體偵測：YOLO(即時)/Faster R-CNN。語意分割逐像素分類。Vision Transformer(ViT)將transformer引入視覺。應用：自駕/醫學影像/監控/AR。CLIP連接圖像和文字。"),

    (["generative AI","生成式AI","GPT","diffusion","LLM"],
     "generative AI|生成式AI|GPT|diffusion|LLM",
     "生成式AI創造新內容。LLM(GPT/Claude/LLaMA)基於transformer和大規模預訓練。Diffusion models(Stable Diffusion/DALL-E/Midjourney)從噪聲逐步生成圖像。GAN生成器vs判別器對抗訓練。多模態模型(GPT-4V/Gemini)同時處理文字和影像。Scaling laws：更多數據+更大模型→更好性能。Emergent abilities出現在大規模模型中。RLHF用人類回饋對齊模型。"),

    # ===== Music =====
    (["music theory advanced","和聲","counterpoint","曲式","key","modulation"],
     "music theory advanced|和聲|對位法|曲式|調性|轉調",
     "和聲學：和弦功能—主和弦(I)/屬和弦(V)/下屬(IV)。對位法：多聲部獨立旋律的結合(巴赫賦格是巔峰)。奏鳴曲式：呈示部/發展部/再現部。十二音列(荀伯格)打破調性。爵士和聲：延伸和弦(9th/11th/13th)/和弦替代/即興。調式(Dorian/Mixolydian等)提供不同色彩。"),

    # ===== Linguistics =====
    (["linguistics","語言學","grammar","syntax","phonology","semantics"],
     "linguistics|語言學|語法|語意|語用|音韻",
     "語言學科學研究人類語言。子領域：音韻學(語音系統)/構詞學(詞結構)/句法學(句子結構)/語意學(意義)/語用學(語境中的使用)。Chomsky生成語法：語言是先天能力(普遍語法UG)。~7000種語言，許多瀕危。語系：印歐(最多說者)/漢藏/閃含/尼日爾-剛果。Sapir-Whorf假說：語言影響思維。手語是完整的自然語言。"),

    # ===== HCI =====
    (["HCI","人機互動","UX","UI","usability","interface design"],
     "HCI|人機互動|UX|UI|usability|介面設計",
     "人機互動(HCI)研究人與電腦的互動設計。UX(使用者體驗)涵蓋整體感受，UI(使用者介面)側重視覺和互動。Nielsen十大易用性原則：一致性/錯誤預防/回饋/效率等。響應式設計適應不同裝置。無障礙設計(WCAG)確保所有人都能使用。Design thinking：同理→定義→發想→原型→測試。A/B testing用數據驅動設計決策。"),

    # ===== World Cuisine (expanded) =====
    (["world cuisine","世界料理","cooking tradition","gastronomy"],
     "world cuisine|世界料理|烹飪傳統|美食學",
     "法式料理：五大母醬，精緻Fine Dining。日式：壽司/刺身/拉麵/天婦羅，重鮮味umami和季節感。中式八大菜系：川菜麻辣/粵菜清鮮/魯菜醬香/蘇菜精緻。義大利：300+種pasta各配不同醬。泰式：酸甜辣鹹平衡。印度：香料王國curry/biryani/tandoori。墨西哥：taco/guacamole/mole。韓式：泡菜/拌飯/烤肉。中東：kebab/hummus/falafel。"),

    # ===== Architecture =====
    (["architecture","建築","building design","skyscraper","style"],
     "architecture|建築|建築設計|摩天大樓|風格",
     "建築風格演變：古代(金字塔/神廟)→古典(希臘柱式/羅馬拱券)→哥德(尖拱/飛扶壁/大教堂)→文藝復興(對稱/穹頂)→巴洛克(華麗)→新古典→Art Nouveau→Art Deco→現代(包浩斯/less is more)→後現代→當代。最高：哈里發塔828m。永續建築：綠屋頂/被動式節能/LEED認證。知名建築師：萊特/柯比意/乘丹下/安藤忠雄/乘哈蒂。"),

    # ===== Agriculture =====
    (["agriculture","農業","farming","crop","food security"],
     "agriculture|農業|farming|作物|糧食安全",
     "農業養活80億人。綠色革命(1960s)：高產品種/化肥/灌溉大幅增產。主要作物：稻米/小麥/玉米/大豆。現代技術：精準農業(GPS/感測器)/垂直農場/水耕/魚菜共生。挑戰：氣候變遷/土壤退化/水資源短缺/生物多樣性喪失/抗藥性。有機農業避免合成化學品。基改作物增產但有爭議。全球~30%食物被浪費。台灣推動地產地消和食農教育。"),

    # ===== Materials Science =====
    (["materials science","材料科學","metal","ceramic","polymer","composite"],
     "materials science|材料科學|金屬|陶瓷|聚合物|複合材料",
     "材料科學研究結構-性質關係。金屬：強韌/導電/可延展(鋼/鋁/鈦)。陶瓷：硬/耐熱/脆(玻璃/碳化矽)。聚合物：輕/柔韌(塑膠/橡膠/纖維)。複合材料結合優點(碳纖維增強聚合物/玻璃纖維/混凝土)。智慧材料：形狀記憶合金/壓電材料/自癒合材料。生物材料用於醫療植入物。超材料：工程結構賦予自然界不存在的性質。"),
]

print(f"Reading {FILE}...")
with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Find the end of COMPRESSED_KB - look for the ] before def __init__
# Strategy: find "def __init__(self):" that comes after COMPRESSED_KB
kb_start = content.find("COMPRESSED_KB = [")
if kb_start == -1:
    msg = "FATAL: COMPRESSED_KB not found!"
    print(msg)
    with open(LOG, "w", encoding="utf-8") as f:
        f.write(msg)
    exit(1)

# Find the def __init__ after COMPRESSED_KB
init_pos = content.find("def __init__(self):", kb_start)
if init_pos == -1:
    msg = "FATAL: def __init__ not found after COMPRESSED_KB!"
    print(msg)
    with open(LOG, "w", encoding="utf-8") as f:
        f.write(msg)
    exit(1)

# Find the ] that closes COMPRESSED_KB (last ] before def __init__)
# Search backwards from init_pos
search_region = content[kb_start:init_pos]
last_bracket = search_region.rfind("]")
if last_bracket == -1:
    msg = "FATAL: Closing ] not found!"
    print(msg)
    with open(LOG, "w", encoding="utf-8") as f:
        f.write(msg)
    exit(1)

# Absolute position
bracket_abs = kb_start + last_bracket

# Build new entries
new_str = "\n        # ══════════════════════════════════════════════\n"
new_str += "        # 🌐 V57 擴充知識庫 — Batch 5 (Math/CS/Law/Religion/Art/Env/Phil/Physics/Psych/AI)\n"
new_str += "        # ══════════════════════════════════════════════\n"

for tags_list, patterns, answer in NEW_ENTRIES:
    # Format tags as Python list
    if isinstance(tags_list, list):
        tags_str = "[" + ",".join(f'"{t}"' for t in tags_list) + "]"
    else:
        tags_str = f'"{tags_list}"'
    new_str += f'        ({tags_str},\n'
    new_str += f'         "{patterns}",\n'
    new_str += f'         "{answer}"),\n\n'

# Insert before the closing ]
new_content = content[:bracket_abs] + new_str + content[bracket_abs:]

print(f"Writing updated file...")
with open(FILE, "w", encoding="utf-8") as f:
    f.write(new_content)

# Count entries
new_kb_start = new_content.find("COMPRESSED_KB = [")
new_init = new_content.find("def __init__(self):", new_kb_start)
new_kb = new_content[new_kb_start:new_init]
count = new_kb.count('"),')

new_lines = new_content.count('\n') + 1

result = f"SUCCESS! Added {len(NEW_ENTRIES)} entries (Batch 5)\nTotal KB entries: {count}\nNew file lines: {new_lines}\n"
print(result)
with open(LOG, "w", encoding="utf-8") as f:
    f.write(result)
