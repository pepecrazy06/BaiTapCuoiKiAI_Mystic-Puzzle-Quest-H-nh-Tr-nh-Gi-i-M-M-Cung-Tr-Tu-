"""
Graph dữ liệu cho UTE Treasure Pathfinder.

Bản belief_dungeon_v6:
- Route về Goal ưu tiên đi ngang qua HGL02 để kích hoạt hầm ngục sương mù.
- Goal vẫn chỉ vào được qua 3 cổng: GATE_MID, B09, G04.
"""

from __future__ import annotations

from math import hypot
from typing import Dict, List

MAP_W = 1448
MAP_H = 1086

DEFAULT_START = "S"
DEFAULT_GOAL = "GOAL"

# Rule mở rương:
# Rương ở GOAL chỉ mở khi route đã đi qua đủ 3 node tím này.
PURPLE_REQUIRED_NODES = ["DUN02", "HGL02", "FB04"]

NODES = {'S': {'name': 'KTX D - Start', 'x': 826.2, 'y': 170.5, 'kind': 'start'}, 'TOP01': {'name': 'Lối KTX trên 1', 'x': 784.7, 'y': 166.4}, 'TOP02': {'name': 'Lối KTX trên 2', 'x': 725.7, 'y': 158.5}, 'TOP03': {'name': 'Lối KTX trên 3', 'x': 699.5, 'y': 154.9}, 'TOP04': {'name': 'Lối KTX trên 4', 'x': 657.5, 'y': 153.0}, 'L01': {'name': 'Tuyến trái 01', 'x': 647.9, 'y': 176.5}, 'L02': {'name': 'Tuyến trái 02', 'x': 643.2, 'y': 200.5}, 'L03': {'name': 'Tuyến trái 03', 'x': 636.9, 'y': 226.1}, 'L04': {'name': 'Tuyến trái 04', 'x': 628.8, 'y': 251.3}, 'L05': {'name': 'Tuyến trái 05', 'x': 623.5, 'y': 276.9}, 'L06': {'name': 'Tuyến trái 06', 'x': 614.5, 'y': 308.5}, 'L07': {'name': 'Tuyến trái 07', 'x': 607.0, 'y': 332.6}, 'L08': {'name': 'Tuyến trái 08', 'x': 601.7, 'y': 358.2}, 'L09': {'name': 'Tuyến trái 09', 'x': 594.9, 'y': 383.8}, 'L10': {'name': 'Tuyến trái 10', 'x': 586.7, 'y': 405.7}, 'L11': {'name': 'Tuyến trái 11', 'x': 579.1, 'y': 432.0}, 'L12': {'name': 'Tuyến trái 12', 'x': 570.9, 'y': 459.1}, 'L13': {'name': 'Tuyến trái 13', 'x': 563.3, 'y': 485.4}, 'L14': {'name': 'Tuyến trái 14', 'x': 557.3, 'y': 506.5}, 'L15': {'name': 'Tuyến trái 15', 'x': 555.0, 'y': 530.6}, 'L16': {'name': 'Tuyến trái 16', 'x': 547.5, 'y': 554.7}, 'L17': {'name': 'Tuyến trái 17', 'x': 540.0, 'y': 576.5}, 'L18': {'name': 'Tuyến trái 18', 'x': 538.5, 'y': 602.1}, 'L19': {'name': 'Tuyến trái 19', 'x': 531.7, 'y': 622.4}, 'L20': {'name': 'Tuyến trái 20', 'x': 527.9, 'y': 656.3}, 'C01': {'name': 'Lối trung tâm 01', 'x': 549.8, 'y': 684.9}, 'C02': {'name': 'Lối trung tâm 02', 'x': 570.1, 'y': 698.5}, 'C03': {'name': 'Lối trung tâm 03', 'x': 561.1, 'y': 726.3}, 'C04': {'name': 'Lối trung tâm 04', 'x': 556.5, 'y': 748.9}, 'C05': {'name': 'Lối trung tâm 05', 'x': 547.5, 'y': 778.8}, 'C06': {'name': 'Lối trung tâm 06', 'x': 543.0, 'y': 819.5}, 'C07': {'name': 'Lối ngang A 01', 'x': 509.9, 'y': 816.5}, 'C08': {'name': 'Lối ngang A 02', 'x': 477.5, 'y': 811.2}, 'C09': {'name': 'Lối ngang A 03', 'x': 447.4, 'y': 808.9}, 'C10': {'name': 'Lối ngang A 04', 'x': 425.6, 'y': 803.7}, 'C11': {'name': 'Lối trên E1', 'x': 430.1, 'y': 774.3}, 'C12': {'name': 'Lối hầm ngục phải', 'x': 429.3, 'y': 738.9}, 'B01': {'name': 'Lối xuống A 01', 'x': 536.2, 'y': 842.1}, 'B02': {'name': 'Lối xuống A 02', 'x': 531.7, 'y': 878.2}, 'B03': {'name': 'Lối xuống A 03', 'x': 555.0, 'y': 903.8}, 'B04': {'name': 'Lối xuống A 04', 'x': 580.6, 'y': 928.6}, 'B05': {'name': 'Lối cổng chính', 'x': 607.0, 'y': 964.0}, 'B06': {'name': 'Cổng chính', 'x': 716.1, 'y': 1011.4}, 'B07': {'name': 'Lối phải cổng 01', 'x': 719.1, 'y': 932.4}, 'B08': {'name': 'Lối phải cổng 02', 'x': 721.4, 'y': 896.3}, 'B09': {'name': 'Lối phải cổng 03', 'x': 723.7, 'y': 864.6}, 'GOAL': {'name': 'Khối A.1 - Goal', 'x': 729.7, 'y': 828.5, 'kind': 'goal'}, 'G01': {'name': 'Lối trái Goal 01', 'x': 683.8, 'y': 882.7}, 'G02': {'name': 'Lối trái Goal 02', 'x': 649.1, 'y': 858.6}, 'G03': {'name': 'Lối trái Goal 03', 'x': 635.6, 'y': 833.0}, 'G04': {'name': 'Lối trái Goal 04', 'x': 683.8, 'y': 835.3}, 'R01': {'name': 'Lối phải A 01', 'x': 761.3, 'y': 893.2}, 'R02': {'name': 'Lối phải A 02', 'x': 792.2, 'y': 880.4}, 'R03': {'name': 'Lối phải A 03', 'x': 817.8, 'y': 853.3}, 'R04': {'name': 'Lối phải A 04', 'x': 852.4, 'y': 855.6}, 'R05': {'name': 'Lối phải A 05', 'x': 881.0, 'y': 861.6}, 'R06': {'name': 'Ngõ cụt phải 01', 'x': 832.8, 'y': 1007.7}, 'R07': {'name': 'Ngõ cụt phải 02', 'x': 877.2, 'y': 1009.2}, 'R08': {'name': 'Ngõ cụt phải 03', 'x': 887.0, 'y': 982.1}, 'R09': {'name': 'Ngõ cụt phải 04', 'x': 894.5, 'y': 958.7}, 'R10': {'name': 'Ngõ cụt phải 05', 'x': 899.8, 'y': 925.6}, 'R11': {'name': 'Ngõ cụt phải 06', 'x': 908.8, 'y': 882.7}, 'DUN01': {'name': 'Lối vào hầm ngục', 'x': 394.7, 'y': 727.1}, 'DUN02': {'name': 'Hầm ngục', 'x': 362.3, 'y': 722.6}, 'DUN03': {'name': 'Lối hầm ngục 03', 'x': 358.6, 'y': 791.1}, 'DUN04': {'name': 'Lối hầm ngục 04', 'x': 360.8, 'y': 759.5}, 'DUN05': {'name': 'Lối hầm ngục 05', 'x': 325.5, 'y': 792.6}, 'LB01': {'name': 'Ngã ba khu E', 'x': 277.3, 'y': 782.1}, 'LB02': {'name': 'Lối E dưới 01', 'x': 272.8, 'y': 806.9}, 'LB03': {'name': 'Lối E trái 01', 'x': 249.4, 'y': 771.5}, 'LB04': {'name': 'Lối E trái 02', 'x': 203.5, 'y': 764.0}, 'LB05': {'name': 'Lối E trái 03', 'x': 167.4, 'y': 774.5}, 'LB06': {'name': 'Lối E trái 04', 'x': 132.8, 'y': 776.8}, 'LB07': {'name': 'Lối E trái 05', 'x': 122.2, 'y': 801.6}, 'LB08': {'name': 'Lối E trái 06', 'x': 115.4, 'y': 832.5}, 'LB09': {'name': 'Lối E trái 07', 'x': 114.7, 'y': 861.9}, 'LB10': {'name': 'Lối E trái 08', 'x': 110.9, 'y': 889.7}, 'LB11': {'name': 'Lối E trái 09', 'x': 109.4, 'y': 922.8}, 'LB12': {'name': 'Lối xưởng máy 01', 'x': 150.1, 'y': 942.4}, 'LB13': {'name': 'Xưởng máy', 'x': 198.2, 'y': 937.1}, 'LB14': {'name': 'Lối xưởng máy 02', 'x': 236.6, 'y': 947.7}, 'LB15': {'name': 'Ngã ba xưởng máy', 'x': 263.7, 'y': 946.2}, 'LB16': {'name': 'Lối bảo vệ', 'x': 313.4, 'y': 943.9}, 'LB17': {'name': 'Ngõ cụt trái', 'x': 366.9, 'y': 954.5}, 'LB18': {'name': 'Lối E dưới 02', 'x': 270.5, 'y': 858.9}, 'LB19': {'name': 'Lối E dưới 03', 'x': 266.7, 'y': 898.8}, 'F01': {'name': 'Lối hội trường 01', 'x': 603.2, 'y': 695.0}, 'F02': {'name': 'Lối hội trường 02', 'x': 643.1, 'y': 697.3}, 'F03': {'name': 'Lối hội trường 03', 'x': 680.0, 'y': 701.8}, 'F04': {'name': 'Đài phun nước - ngã tư', 'x': 622.8, 'y': 646.9}, 'F05': {'name': 'Lối khoa máy 01', 'x': 575.4, 'y': 621.3}, 'F06': {'name': 'Lối hội trường 04', 'x': 654.4, 'y': 661.9}, 'F07': {'name': 'Lối hội trường 05', 'x': 658.7, 'y': 636.0}, 'F08': {'name': 'Ngã ba hội trường', 'x': 691.9, 'y': 623.3}, 'F09': {'name': 'Khoa máy', 'x': 617.2, 'y': 606.2}, 'F10': {'name': 'Lối khoa máy 02', 'x': 651.0, 'y': 615.0}, 'HGL01': {'name': 'Lối hầm ngục lớn 01', 'x': 711.4, 'y': 705.4}, 'HGL02': {'name': 'Hầm ngục lớn', 'x': 750.6, 'y': 700.6}, 'HGL03': {'name': 'Lối hầm ngục lớn 03', 'x': 787.1, 'y': 715.0}, 'HGL04': {'name': 'Ngã ba hầm ngục lớn', 'x': 815.3, 'y': 717.2}, 'HGL05': {'name': 'Lối sang Khối G 01', 'x': 860.1, 'y': 723.3}, 'HGL06': {'name': 'Lối sang Khối G 02', 'x': 903.8, 'y': 729.9}, 'HGL07': {'name': 'Lối sang Khối G 03', 'x': 938.1, 'y': 736.5}, 'HGL08': {'name': 'Lối xuống G 01', 'x': 932.6, 'y': 766.4}, 'HGL09': {'name': 'Lối xuống G 02', 'x': 927.0, 'y': 799.6}, 'HGL10': {'name': 'Lối xuống G 03', 'x': 921.2, 'y': 826.8}, 'HGL11': {'name': 'Ngã ba khu G', 'x': 916.2, 'y': 860.0}, 'RG01': {'name': 'Lối Khối G 01', 'x': 969.9, 'y': 745.8}, 'RG02': {'name': 'Khối G', 'x': 1028.0, 'y': 740.6}, 'RG03': {'name': 'Lối Khối G 03', 'x': 1066.8, 'y': 755.2}, 'RG04': {'name': 'Lối Khối G 04', 'x': 1128.4, 'y': 761.5}, 'RG05': {'name': 'Lối xưởng phải 01', 'x': 1132.9, 'y': 724.7}, 'RG06': {'name': 'Lối xưởng phải 02', 'x': 1144.9, 'y': 676.4}, 'RG07': {'name': 'Lối xưởng phải 03', 'x': 1130.7, 'y': 643.0}, 'RG08': {'name': 'Lối xưởng phải 04', 'x': 1128.4, 'y': 637.3}, 'RG09': {'name': 'Lối xưởng phải 05', 'x': 1159.5, 'y': 608.3}, 'RG10': {'name': 'Lối xưởng phải 06', 'x': 1167.8, 'y': 571.8}, 'RG11': {'name': 'Lối xưởng phải 07', 'x': 1181.1, 'y': 528.1}, 'RG12': {'name': 'Lối xưởng phải 08', 'x': 1220.3, 'y': 530.4}, 'RG13': {'name': 'Ngõ cụt xưởng phải', 'x': 1250.7, 'y': 524.8}, 'UR01': {'name': 'Ngã ba xưởng phải trên', 'x': 1194.3, 'y': 480.0}, 'UR02': {'name': 'Lối xưởng phải trên 02', 'x': 1201.5, 'y': 448.5}, 'UR03': {'name': 'Lối xưởng phải trên 03', 'x': 1206.5, 'y': 414.8}, 'UR04': {'name': 'Ngã ba tường phải', 'x': 1212.0, 'y': 383.8}, 'UR05': {'name': 'Lối tường phải 05', 'x': 1171.7, 'y': 371.7}, 'UR06': {'name': 'Lối tường phải 06', 'x': 1134.6, 'y': 374.4}, 'UR07': {'name': 'Lối tường phải 07', 'x': 1089.8, 'y': 362.8}, 'UR08': {'name': 'Lối tường phải 08', 'x': 1055.0, 'y': 359.5}, 'UR09': {'name': 'Lối tường phải 09', 'x': 1021.3, 'y': 356.2}, 'UR10': {'name': 'Hành lang phải 10', 'x': 1012.4, 'y': 383.8}, 'UR11': {'name': 'Hành lang phải 11', 'x': 1006.4, 'y': 418.6}, 'UR12': {'name': 'Hành lang phải 12', 'x': 1002.5, 'y': 455.1}, 'UR13': {'name': 'Hành lang phải 13', 'x': 994.7, 'y': 485.5}, 'UR14': {'name': 'Hành lang phải 14', 'x': 989.8, 'y': 518.7}, 'UR15': {'name': 'Hành lang phải 15', 'x': 984.8, 'y': 551.9}, 'UR16': {'name': 'Hành lang phải 16', 'x': 976.5, 'y': 583.4}, 'UR17': {'name': 'Hành lang phải 17', 'x': 968.8, 'y': 617.7}, 'UR18': {'name': 'Hành lang phải 18', 'x': 961.0, 'y': 646.4}, 'UR19': {'name': 'Hành lang phải 19', 'x': 951.6, 'y': 689.0}, 'SV01': {'name': 'Lối dịch vụ 01', 'x': 1167.8, 'y': 771.8}, 'SV02': {'name': 'Lối dịch vụ 02', 'x': 1224.2, 'y': 775.7}, 'SV03': {'name': 'Ngõ cụt dịch vụ', 'x': 1281.7, 'y': 785.6}, 'FB01': {'name': 'Lối sân bóng 01', 'x': 931.2, 'y': 959.7}, 'FB02': {'name': 'Lối sân bóng 02', 'x': 976.7, 'y': 960.6}, 'FB03': {'name': 'Sân bóng', 'x': 989.8, 'y': 913.1}, 'FB04': {'name': 'Lối sân bóng phải', 'x': 1091.9, 'y': 860.2}, 'TR01': {'name': 'Lối phòng thí nghiệm 01', 'x': 1024.9, 'y': 327.2}, 'TR02': {'name': 'Lối phòng thí nghiệm 02', 'x': 1032.2, 'y': 290.3}, 'TR03': {'name': 'Ngã ba phòng thí nghiệm', 'x': 1033.6, 'y': 255.3}, 'TR04': {'name': 'Lối y tế phải 01', 'x': 1002.2, 'y': 244.3}, 'TR05': {'name': 'Lối y tế phải 02', 'x': 966.5, 'y': 237.8}, 'TR06': {'name': 'Lối căn tin 01', 'x': 1079.6, 'y': 237.8}, 'TR07': {'name': 'Lối căn tin 02', 'x': 1138.8, 'y': 214.4}, 'TR08': {'name': 'Lối căn tin 03', 'x': 1162.5, 'y': 237.2}, 'TR09': {'name': 'Lối căn tin 04', 'x': 1143.5, 'y': 252.7}, 'TR10': {'name': 'Ngõ cụt căn tin', 'x': 1161.9, 'y': 282.6}, 'M01': {'name': 'Lối hội trường lớn 01', 'x': 687.5, 'y': 658.7}, 'M02': {'name': 'Lối sân mái vòm 01', 'x': 824.5, 'y': 664.9}, 'M03': {'name': 'Lối sân mái vòm 02', 'x': 830.9, 'y': 634.2}, 'M04': {'name': 'Lối sân mái vòm 03', 'x': 816.8, 'y': 613.1}, 'M05': {'name': 'Lối sân mái vòm 04', 'x': 793.8, 'y': 604.8}, 'M06': {'name': 'Lối HSSV 01', 'x': 834.1, 'y': 582.4}, 'M07': {'name': 'Lối HSSV 02', 'x': 800.9, 'y': 565.2}, 'M08': {'name': 'Ngã ba thư viện - HSSV', 'x': 774.0, 'y': 553.7}, 'M09': {'name': 'Lối HSSV 03', 'x': 837.9, 'y': 565.2}, 'M10': {'name': 'Ngã ba Khối A', 'x': 738.9, 'y': 555.6}, 'M11': {'name': 'Lối Khối A 01', 'x': 763.2, 'y': 607.4}, 'M12': {'name': 'Lối Khối A 02', 'x': 721.0, 'y': 605.4}, 'M13': {'name': 'Lối Khối A 03', 'x': 699.9, 'y': 577.3}, 'M14': {'name': 'Ngã tư Khối A', 'x': 701.2, 'y': 549.2}, 'M15': {'name': 'Lối thư viện trái 01', 'x': 669.2, 'y': 545.4}, 'M16': {'name': 'Lối thư viện trái 02', 'x': 623.9, 'y': 535.8}, 'M17': {'name': 'Lối thư viện trái 03', 'x': 588.1, 'y': 535.8}, 'M18': {'name': 'Lối thư viện bắc 01', 'x': 703.1, 'y': 502.6}, 'M19': {'name': 'Lối thư viện bắc 02', 'x': 711.4, 'y': 466.2}, 'M20': {'name': 'Lối thư viện bắc 03', 'x': 717.2, 'y': 429.1}, 'M21': {'name': 'Lối thư viện bắc 04', 'x': 724.2, 'y': 401.0}, 'M22': {'name': 'Lối khối C-B 01', 'x': 694.1, 'y': 393.9}, 'M23': {'name': 'Lối khối C-B 02', 'x': 658.4, 'y': 390.8}, 'M24': {'name': 'Lối khối C-B 03', 'x': 627.1, 'y': 386.3}, 'M25': {'name': 'Lối khối B 01', 'x': 730.6, 'y': 376.1}, 'M26': {'name': 'Lối khối B 02', 'x': 740.2, 'y': 352.4}, 'M27': {'name': 'Lối khối C trên 01', 'x': 713.3, 'y': 347.3}, 'M28': {'name': 'Lối khối C trên 02', 'x': 678.2, 'y': 337.1}, 'M29': {'name': 'Lối khối C trên 03', 'x': 643.7, 'y': 337.1}, 'M30': {'name': 'Lối khối B trên 01', 'x': 772.7, 'y': 354.3}, 'M31': {'name': 'Lối khối B trên 02', 'x': 822.6, 'y': 351.8}, 'M32': {'name': 'Lối y tế 01', 'x': 854.5, 'y': 363.3}, 'M33': {'name': 'Ngã ba y tế', 'x': 902.4, 'y': 369.7}, 'M34': {'name': 'Lối y tế 02', 'x': 912.0, 'y': 315.0}, 'M35': {'name': 'Lối y tế 03', 'x': 918.4, 'y': 265.2}, 'M36': {'name': 'Ngã ba y tế trên', 'x': 926.1, 'y': 237.7}, 'M37': {'name': 'Lối KTX phải 01', 'x': 931.8, 'y': 201.9}, 'M38': {'name': 'Ngã ba KTX phải', 'x': 933.8, 'y': 181.5}, 'M39': {'name': 'Lối KTX phải 02', 'x': 896.7, 'y': 173.8}, 'M40': {'name': 'Lối KTX phải 03', 'x': 864.1, 'y': 171.3}, 'M41': {'name': 'Lối KTX phải 04', 'x': 976.6, 'y': 176.5}, 'M42': {'name': 'Ngõ cụt KTX phải', 'x': 1027.0, 'y': 181.2}, 'HS01': {'name': 'Ngã ba HSSV', 'x': 859.4, 'y': 566.4}, 'HS02': {'name': 'Lối HSSV phải 01', 'x': 898.8, 'y': 570.3}, 'HS03': {'name': 'Lối HSSV phải 02', 'x': 942.8, 'y': 575.9}, 'HS04': {'name': 'Lối HSSV trên 01', 'x': 861.0, 'y': 534.2}, 'HS05': {'name': 'Lối HSSV trên 02', 'x': 869.4, 'y': 499.1}, 'HS06': {'name': 'Lối HSSV trên 03', 'x': 877.7, 'y': 469.1}, 'HS07': {'name': 'Ngõ cụt HSSV', 'x': 884.9, 'y': 437.1}, 'MIDR01': {'name': 'Lối phải giữa 01', 'x': 1063.7, 'y': 462.0}, 'MIDR02': {'name': 'Lối phải giữa 02', 'x': 1124.0, 'y': 469.9}, 'GATE_MID': {'name': 'Cổng vào kho báu giữa', 'x': 775.0, 'y': 845.6, 'kind': 'goal_gate'}, 'N_DUN_LINK': {'name': 'Node nối C10 - DUN03', 'x': 391.4, 'y': 799.5}}

EDGE_DATA = [('S', 'TOP01'), ('TOP01', 'TOP02'), ('TOP02', 'TOP03'), ('TOP03', 'TOP04'), ('TOP04', 'L01'), ('L01', 'L02'), ('L02', 'L03'), ('L03', 'L04'), ('L04', 'L05'), ('L05', 'L06'), ('L06', 'L07'), ('L07', 'L08'), ('L08', 'L09'), ('L09', 'L10'), ('L10', 'L11'), ('L11', 'L12'), ('L12', 'L13'), ('L13', 'L14'), ('L14', 'L15'), ('L15', 'L16'), ('L16', 'L17'), ('L17', 'L18'), ('L18', 'L19'), ('L19', 'L20'), ('L20', 'C01'), ('C01', 'C02'), ('C02', 'F01'), ('F01', 'F02'), ('F02', 'F03'), ('C02', 'C03'), ('C03', 'C04'), ('C04', 'C05'), ('C05', 'C06'), ('C06', 'B01'), ('B01', 'B02'), ('B02', 'B03'), ('B03', 'B04'), ('B04', 'B05'), ('B05', 'B06'), ('B06', 'B07'), ('B07', 'B08'), ('B08', 'B09'), ('B09', 'GOAL'), ('B09', 'G01'), ('G01', 'G02'), ('G02', 'G03'), ('G03', 'G04'), ('G04', 'GOAL'), ('R01', 'R02'), ('R02', 'R03'), ('R03', 'R04'), ('R04', 'R05'), ('R05', 'R11'), ('R11', 'R10'), ('R10', 'R09'), ('R09', 'R08'), ('R08', 'R07'), ('R07', 'R06'), ('C06', 'C07'), ('C07', 'C08'), ('C08', 'C09'), ('C09', 'C10'), ('C10', 'C11'), ('C11', 'C12'), ('C12', 'DUN01'), ('DUN01', 'DUN02'), ('DUN02', 'DUN04'), ('DUN04', 'DUN03'), ('DUN03', 'DUN05'), ('DUN05', 'LB01'), ('LB01', 'LB03'), ('LB03', 'LB04'), ('LB04', 'LB05'), ('LB05', 'LB06'), ('LB06', 'LB07'), ('LB07', 'LB08'), ('LB08', 'LB09'), ('LB09', 'LB10'), ('LB10', 'LB11'), ('LB11', 'LB12'), ('LB12', 'LB13'), ('LB13', 'LB14'), ('LB14', 'LB15'), ('LB15', 'LB16'), ('LB16', 'LB17'), ('LB01', 'LB02'), ('LB02', 'LB18'), ('LB18', 'LB19'), ('LB19', 'LB15'), ('L18', 'F09'), ('F09', 'F10'), ('F10', 'F07'), ('F07', 'F08'), ('F09', 'F05'), ('F05', 'F04'), ('F04', 'F06'), ('F06', 'F08'), ('F04', 'F01'), ('F06', 'F02'), ('F03', 'HGL01'), ('HGL01', 'HGL02'), ('HGL02', 'HGL03'), ('HGL03', 'HGL04'), ('HGL04', 'HGL05'), ('HGL05', 'HGL06'), ('HGL06', 'HGL07'), ('HGL07', 'HGL08'), ('HGL08', 'HGL09'), ('HGL09', 'HGL10'), ('HGL10', 'HGL11'), ('RG01', 'RG02'), ('RG02', 'RG03'), ('RG03', 'RG04'), ('RG04', 'RG05'), ('RG05', 'RG06'), ('RG06', 'RG07'), ('RG07', 'RG08'), ('RG08', 'RG09'), ('RG09', 'RG10'), ('RG10', 'RG11'), ('RG11', 'RG12'), ('RG12', 'RG13'), ('RG11', 'UR01'), ('UR01', 'UR02'), ('UR02', 'UR03'), ('UR03', 'UR04'), ('UR04', 'UR05'), ('UR05', 'UR06'), ('UR06', 'UR07'), ('UR07', 'UR08'), ('UR08', 'UR09'), ('UR09', 'UR10'), ('UR10', 'UR11'), ('UR11', 'UR12'), ('UR12', 'UR13'), ('UR13', 'UR14'), ('UR14', 'UR15'), ('UR15', 'UR16'), ('UR16', 'UR17'), ('UR17', 'UR18'), ('UR18', 'UR19'), ('RG04', 'SV01'), ('SV01', 'SV02'), ('SV02', 'SV03'), ('FB01', 'FB02'), ('FB02', 'FB03'), ('FB03', 'FB04'), ('FB04', 'RG04'), ('FB04', 'SV01'), ('UR09', 'TR01'), ('TR01', 'TR02'), ('TR02', 'TR03'), ('TR03', 'TR04'), ('TR04', 'TR05'), ('TR05', 'M36'), ('TR03', 'TR06'), ('TR06', 'TR07'), ('TR07', 'TR08'), ('TR08', 'TR09'), ('TR09', 'TR10'), ('TR06', 'TR09'), ('M38', 'M41'), ('M41', 'M42'), ('F08', 'M01'), ('M01', 'HGL01'), ('M01', 'F04'), ('M02', 'M03'), ('M03', 'M04'), ('M04', 'M05'), ('M05', 'M11'), ('M11', 'M12'), ('M12', 'F08'), ('M05', 'M06'), ('M06', 'M07'), ('M07', 'M08'), ('M08', 'M10'), ('M10', 'M13'), ('M13', 'M14'), ('M06', 'M09'), ('M09', 'HS01'), ('M10', 'M11'), ('M14', 'M15'), ('M15', 'M16'), ('M16', 'M17'), ('M17', 'L15'), ('M14', 'M18'), ('M18', 'M19'), ('M19', 'M20'), ('M20', 'M21'), ('M21', 'M22'), ('M22', 'M23'), ('M23', 'M24'), ('M24', 'L09'), ('M21', 'M25'), ('M25', 'M26'), ('M26', 'M27'), ('M27', 'M28'), ('M28', 'M29'), ('M29', 'L07'), ('M26', 'M30'), ('M30', 'M31'), ('M31', 'M32'), ('M32', 'M33'), ('M33', 'M34'), ('M34', 'M35'), ('M35', 'M36'), ('M36', 'M37'), ('M37', 'M38'), ('M38', 'M39'), ('M39', 'M40'), ('M40', 'S'), ('M33', 'UR10'), ('HS01', 'HS02'), ('HS02', 'HS03'), ('HS03', 'UR16'), ('HS01', 'HS04'), ('HS04', 'HS05'), ('HS05', 'HS06'), ('HS06', 'HS07'), ('HS03', 'UR19'), ('UR12', 'MIDR01'), ('MIDR01', 'MIDR02'), ('MIDR02', 'UR01'), ('MIDR01', 'UR13'), ('GATE_MID', 'GOAL'), ('GATE_MID', 'R01'), ('GATE_MID', 'R03'), ('GATE_MID', 'HGL11'), ('C10', 'N_DUN_LINK'), ('N_DUN_LINK', 'DUN03')]

EDGE_WAYPOINTS = {}

NO_GO_ZONES = []


def has_xy(node_id: str) -> bool:
    node = NODES.get(node_id)
    return bool(node and node.get("x") is not None and node.get("y") is not None)


def edge_key(a: str, b: str) -> str:
    return f"{a}|{b}"


def edge_points(src: str, dst: str) -> List[dict]:
    if not has_xy(src) or not has_xy(dst):
        return []

    start = NODES[src]
    end = NODES[dst]
    direct_key = edge_key(src, dst)
    reverse_key = edge_key(dst, src)

    if direct_key in EDGE_WAYPOINTS:
        mid = EDGE_WAYPOINTS[direct_key]
    elif reverse_key in EDGE_WAYPOINTS:
        mid = list(reversed(EDGE_WAYPOINTS[reverse_key]))
    else:
        mid = []

    return [
        {"x": start["x"], "y": start["y"]},
        *[{"x": p["x"], "y": p["y"]} for p in mid],
        {"x": end["x"], "y": end["y"]},
    ]


def polyline_distance(points: List[dict]) -> float:
    total = 0.0
    for i in range(1, len(points)):
        total += hypot(points[i]["x"] - points[i - 1]["x"], points[i]["y"] - points[i - 1]["y"])
    return total


def edge_violates_rule(src: str, dst: str) -> bool:
    return False


def build_edges() -> List[dict]:
    edges = []
    for idx, (src, dst) in enumerate(EDGE_DATA, start=1):
        points = edge_points(src, dst)
        if not points:
            continue

        distance = round(polyline_distance(points), 2)
        edges.append({
            "id": f"E{idx:03d}",
            "from": src,
            "to": dst,
            "distance": distance,
            "time": round(distance / 42, 2),
            "risk": 1.0,
            "violates_no_go": edge_violates_rule(src, dst),
            "shape_points": points,
        })
    return edges


def build_adjacency() -> Dict[str, List[dict]]:
    adj = {node_id: [] for node_id in NODES}
    for edge in build_edges():
        adj[edge["from"]].append(edge)
        rev = {
            **edge,
            "id": edge["id"] + "R",
            "from": edge["to"],
            "to": edge["from"],
            "shape_points": list(reversed(edge["shape_points"])),
        }
        adj[edge["to"]].append(rev)

    for edge_list in adj.values():
        edge_list.sort(key=lambda e: (e["violates_no_go"], e["distance"], e["to"]))
    return adj


def graph_payload() -> dict:
    return {
        "map": {"width": MAP_W, "height": MAP_H},
        "nodes": NODES,
        "edges": build_edges(),
        "no_go_zones": NO_GO_ZONES,
        "start": DEFAULT_START,
        "goal": DEFAULT_GOAL,
        "goal_gate_nodes": ["GATE_MID", "B09", "G04"],
        "purple_required_nodes": PURPLE_REQUIRED_NODES,
        "dungeon_trigger_node": "HGL02",
        "ready": has_xy(DEFAULT_START) and has_xy(DEFAULT_GOAL) and len(EDGE_DATA) > 0,
        "rules": [
            "Nhân vật chỉ được di chuyển qua node.",
            "Không được đi xuyên qua tòa nhà, tường, hồ hoặc rừng.",
            "Khi đi ngang qua HGL02, nhân vật sẽ vào hầm ngục sương mù.",
            "Trong hầm ngục, AI dùng Belief State / No Observation để tìm lối ra.",
            "Muốn mở rương ở GOAL, route bắt buộc phải đi qua đủ 3 node tím: DUN02, HGL02, FB04.",
        ],
    }
