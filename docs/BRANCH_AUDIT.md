# Kiểm kê nhánh remote — phần A

Repo: [7roger89-web/logistics-work-desk-arena](https://github.com/7roger89-web/logistics-work-desk-arena).
Thời điểm chụp: **2026-11-02T17:35:44+07:00** (Asia/Saigon, UTC+07:00).
Main đối chiếu: `2829b0e6d64c428abe10b5a2c48e053ba654c530`.

**Chỉ báo cáo. Chưa xoá nhánh, chưa cài skill, chưa sửa AGENTS hoặc projection.**
Dừng sau phần A; chỉ thực hiện phần B khi Owner nói tiếp.

## Cách đo

- Liệt kê toàn bộ `refs/heads/*` đang tồn tại trên GitHub bằng `git ls-remote --heads origin`; không tính tag hoặc remote symbolic HEAD.
- Ngày commit cuối là **committer date** của đúng SHA đầu nhánh (`git show -s --format=%cI`), không phải ngày tạo nhánh hoặc ngày push. Tuổi tính theo thời gian thực từ ngày này tới lúc chụp, không làm tròn trước khi chia nhóm.
- ĐÃ GỘP: SHA đầu nhánh là ancestor của main (`git merge-base --is-ancestor`), hoặc có PR đã merge vào main với **head SHA trùng đầu nhánh hiện tại**. Cách thứ hai nhận diện cả squash/rebase merge; PR cũ có head khác không đủ để kết luận nhánh hiện tại đã gộp.
- CHƯA GỘP: chưa có bằng chứng theo hai tiêu chí trên; không khẳng định mọi thay đổi trên nhánh đều chưa xuất hiện trong main (ví dụ cherry-pick ngoài PR có thể không nhận diện được).
- Nhóm dưới 30 ngày bao gồm mốc đúng 30 ngày; nhóm trên 30 ngày là tuổi lớn hơn 30 × 24 giờ. Tuổi hiển thị hai chữ số thập phân để tham khảo.
- Đọc mọi trang PR bằng GitHub API (`pulls?state=all&per_page=100`) để đánh dấu PR đang mở, kể cả PR nhắm base khác main. Đối chiếu lại toàn bộ tên nhánh và head SHA cuối lượt: không đổi.
- `main` nằm trong ĐÃ GỘP vì tự là ancestor của nó, nhưng **luôn giữ**. Mọi nhánh có PR đang mở cũng **luôn giữ** ở bước xoá phần B.

## Tổng hợp

| Nhóm | Số nhánh |
|---|---:|
| ĐÃ GỘP (gồm main được bảo vệ) | 5 |
| CHƯA GỘP dưới 30 ngày | 119 |
| CHƯA GỘP trên 30 ngày | 12 |
| Tổng remote tại thời điểm chụp | 136 |

Có **4 nhánh ĐÃ GỘP** không phải main và không có PR đang mở tại thời điểm chụp; đây chỉ là ứng viên cho phần B, chưa được xoá. Phải kiểm tra lại main, head SHA và PR đang mở ngay trước khi xoá vì snapshot có thể thay đổi.
Nhánh báo cáo `task/branch-audit-skills` chưa có trên remote tại thời điểm chụp; lần push báo cáo sau đó sẽ thêm một nhánh và không nằm trong tổng snapshot này.

## ĐÃ GỘP

| Nhánh remote | Commit cuối (UTC+07:00) | Tuổi (ngày) | Đã gộp main / bằng chứng | PR đang mở | Bảo vệ | Head SHA |
|---|---|---:|---|---|---|---|
| `arena/38a329f7-logistics-work-desk-arena` | 2026-10-31T16:28:18+07:00 | 2.05 | Git ancestor | — | — | `76cb1b5e242e18ffb4142d496e4b05167d5dacb6` |
| `arena/532dec89-logistics-work-desk-arena` | 2026-10-31T17:39:20+07:00 | 2.00 | Git ancestor | — | — | `15196d4e5624b3d584acd0a7baee42c202408395` |
| `arena/82bbe73c-logistics-work-desk-arena` | 2026-10-31T17:05:52+07:00 | 2.02 | Git ancestor | — | — | `91f5197bdcbd2cece3e9c0f17e90249ce4ce3b9e` |
| `arena/d0cdac49-logistics-work-desk-arena` | 2026-11-01T22:58:31+07:00 | 0.78 | Git ancestor | — | — | `795ad4483824d7acd7405f68a155aa4df0f41496` |
| `main` | 2026-11-01T23:16:46+07:00 | 0.76 | Git ancestor | — | GIỮ: main | `2829b0e6d64c428abe10b5a2c48e053ba654c530` |

## CHƯA GỘP dưới 30 ngày

| Nhánh remote | Commit cuối (UTC+07:00) | Tuổi (ngày) | Đã gộp main / bằng chứng | PR đang mở | Bảo vệ | Head SHA |
|---|---|---:|---|---|---|---|
| `arena/07caf815-logistics-work-desk-arena` | 2026-10-22T11:45:37+07:00 | 11.24 | Không | — | — | `d5989a2b5a95e3b154d3255933185e51ba362556` |
| `arena/09b069e2-logistics-work-desk-arena` | 2026-10-20T15:57:47+07:00 | 13.07 | Không | — | — | `a4c49a0e90694bee48da175980f875eda02f489d` |
| `arena/0d73ca3b-logistics-work-desk-arena` | 2026-11-02T08:39:56+07:00 | 0.37 | Không | — | — | `3b81be703d3cc3e1cf25d7c9bd9e4f317a0929df` |
| `arena/1042ee05-logistics-work-desk-arena` | 2026-10-21T20:37:59+07:00 | 11.87 | Không | — | — | `6093669f0b760502de066a686efe9086f537b86d` |
| `arena/1091a2ef-logistics-work-desk-arena` | 2026-10-23T22:54:56+07:00 | 9.78 | Không | — | — | `93e56533f2ff3326ca3d2e5711bb98b32b3178ba` |
| `arena/138cb56a-logistics-work-desk-arena` | 2026-10-27T23:47:53+07:00 | 5.74 | Không | — | — | `f46c144f3f796689310eca20a9ee2995430dc7cc` |
| `arena/17d7196b-logistics-work-desk-arena` | 2026-10-30T23:25:53+07:00 | 2.76 | Không | — | — | `83edb13ca5ea202c68b7d1b447d7edeff3c926bd` |
| `arena/18ef00cf-logistics-work-desk-arena` | 2026-10-16T17:27:39+07:00 | 17.01 | Không | [#207](https://github.com/7roger89-web/logistics-work-desk-arena/pull/207) | GIỮ: PR đang mở | `7a73e484446bf8ab79f405125d6ba0589e8ab56a` |
| `arena/19b5772e-logistics-work-desk-arena` | 2026-10-21T18:22:46+07:00 | 11.97 | Không | — | — | `b46ec40a42ed04a6db6a496088b4b91b36be052e` |
| `arena/2a9d1865-logistics-work-desk-arena` | 2026-10-16T22:26:32+07:00 | 16.80 | Không | — | — | `11e4f02317d187f2c0a3071d5ecd60266fd6d863` |
| `arena/2aebeae7-logistics-work-desk-arena` | 2026-10-20T23:50:48+07:00 | 12.74 | Không | — | — | `5155b484e0b220d5f1171d6f3945182159fac4ec` |
| `arena/2d829f91-logistics-work-desk-arena` | 2026-11-01T20:02:03+07:00 | 0.90 | Không | — | — | `05b65537bb524b6c0c550f538cce1032f934a6e7` |
| `arena/2e1bd227-logistics-work-desk-arena` | 2026-10-21T16:06:38+07:00 | 12.06 | Không | — | — | `b0aeae6645717c451ff777f97b86e396f9fc9615` |
| `arena/31b6af11-logistics-work-desk-arena` | 2026-11-01T23:02:20+07:00 | 0.77 | Không | — | — | `6934f4b1973aa51d60ddb7936d69651cd58d1590` |
| `arena/325babb5-logistics-work-desk-arena` | 2026-10-19T14:21:05+07:00 | 14.14 | Không | — | — | `bf85c6f4969d4cb50201d8018333eb5b7565a0b0` |
| `arena/36ca27f5-logistics-work-desk-arena` | 2026-10-23T16:08:46+07:00 | 10.06 | Không | — | — | `ac46fb197638b033789c51ec09c9984daffc89e7` |
| `arena/36ed37cb-logistics-work-desk-arena` | 2026-10-20T22:21:39+07:00 | 12.80 | Không | — | — | `4c3c900b9a59a3d773acf4d521ca7ddbaa01ada4` |
| `arena/3851e3be-logistics-work-desk-arena` | 2026-10-16T10:18:07+07:00 | 17.30 | Không | — | — | `5d5e649dba65fa68bf245c922b97e89c3762b2f1` |
| `arena/385e4a4d-logistics-work-desk-arena` | 2026-10-30T17:08:04+07:00 | 3.02 | Không | — | — | `f472274b00cf4849b4837c18d496dfd3dd1e2d33` |
| `arena/3adf0e91-logistics-work-desk-arena` | 2026-10-19T18:56:55+07:00 | 13.94 | Không | — | — | `9b281910e5af1b941259246c14e8973bfac9602c` |
| `arena/3cba5333-logistics-work-desk-arena` | 2026-11-02T01:40:34+07:00 | 0.66 | Không | — | — | `cb1870f95358be3b9e8c6278ac898fc1c9fa2cba` |
| `arena/3de6968f-logistics-work-desk-arena` | 2026-10-21T17:58:57+07:00 | 11.98 | Không | — | — | `6a62e7dfe66d2ed51465592935ebc8803899087a` |
| `arena/438ad5ff-logistics-work-desk-arena` | 2026-10-20T23:09:48+07:00 | 12.77 | Không | — | — | `58477082dda99086ee68713208035c00329686fb` |
| `arena/441d2013-logistics-work-desk-arena` | 2026-10-19T07:43:04+07:00 | 14.41 | Không | — | — | `04fc7c087ab800423a4c90f2c96bbb8734a670cb` |
| `arena/4ff8da97-logistics-work-desk-arena` | 2026-10-21T07:15:38+07:00 | 12.43 | Không | — | — | `3e0770a0041434a2e45f56696408892a65ba9855` |
| `arena/5009c0d2-logistics-work-desk-arena` | 2026-10-22T11:13:53+07:00 | 11.27 | Không | — | — | `2bb443688a5f70582e2c0b37f734f28ba1c92360` |
| `arena/5552b7d0-logistics-work-desk-arena` | 2026-10-21T23:10:43+07:00 | 11.77 | Không | — | — | `8dc182224ce3c3e95bf29b70cb1e8463f75668fa` |
| `arena/56cb5da4-logistics-work-desk-arena` | 2026-10-17T12:08:18+07:00 | 16.23 | Không | [#209](https://github.com/7roger89-web/logistics-work-desk-arena/pull/209) | GIỮ: PR đang mở | `6edf9f3dc73c98bcc61f990368950c5782bcc00a` |
| `arena/577d45f7-logistics-work-desk-arena` | 2026-10-21T22:26:41+07:00 | 11.80 | Không | — | — | `a157d59015af1c12fa7f256d1c96c32cde0a2cca` |
| `arena/5a8ce272-logistics-work-desk-arena` | 2026-10-31T13:22:13+07:00 | 2.18 | Không | — | — | `63f959431b64e0c8a0103bd8214265f71852e6b2` |
| `arena/5b67d6ed-logistics-work-desk-arena` | 2026-10-20T11:09:13+07:00 | 13.27 | Không | — | — | `89e40625f51d79cc1fb47c25dacbf9e5eb112dfc` |
| `arena/5e0c51d4-logistics-work-desk-arena` | 2026-10-22T15:33:36+07:00 | 11.08 | Không | — | — | `ac40097729a0785f7cd5ae78ff7f0d6c37c7cede` |
| `arena/5f43c320-logistics-work-desk-arena` | 2026-10-21T07:29:27+07:00 | 12.42 | Không | — | — | `017f2070500dbc5f110ea1a84fe998502dee49a8` |
| `arena/6008734c-logistics-work-desk-arena` | 2026-10-21T09:45:09+07:00 | 12.33 | Không | — | — | `d6df90d219a6c543cf1a9e5c2f4f258276da50b8` |
| `arena/6286d4a0-logistics-work-desk-arena` | 2026-11-01T17:34:30+07:00 | 1.00 | Không | — | — | `e4273cfcfbc9d38b39f0fbf3212ee8ddfd66a0d5` |
| `arena/6ccf1a57-logistics-work-desk-arena` | 2026-10-19T20:18:13+07:00 | 13.89 | Không | — | — | `d62c9823df3355e6e815a349b7cfb5222e48a8a2` |
| `arena/6db41d2f-logistics-work-desk-arena` | 2026-10-30T12:31:37+07:00 | 3.21 | Không | — | — | `cc9f9a7ae50abe9244ae2a457e5e3dbcb31bcc5a` |
| `arena/6e38f929-logistics-work-desk-arena` | 2026-10-23T13:55:50+07:00 | 10.15 | Không | — | — | `336ea067c9043fe521fcec72bae0af6830488285` |
| `arena/720c23f1-logistics-work-desk-arena` | 2026-11-01T15:39:54+07:00 | 1.08 | Không | — | — | `9239bbeed16d3e2569bd139f4af89a93f9a477a9` |
| `arena/761caa87-logistics-work-desk-arena` | 2026-10-20T23:14:40+07:00 | 12.76 | Không | — | — | `e926edac5cb6bbe6ecacfcdf82916db03d17b46a` |
| `arena/7d8e8372-logistics-work-desk-arena` | 2026-10-16T18:34:39+07:00 | 16.96 | Không | [#208](https://github.com/7roger89-web/logistics-work-desk-arena/pull/208) | GIỮ: PR đang mở | `d293b89c60d3d79ac7f86ccebe1390794ec59ea7` |
| `arena/818a2d0a-logistics-work-desk-arena` | 2026-10-15T17:14:49+07:00 | 18.01 | Không | — | — | `2bf16eabe7e8c75d9be3f90a40e5c99208235416` |
| `arena/8481b579-logistics-work-desk-arena` | 2026-10-23T11:17:26+07:00 | 10.26 | Không | — | — | `96d89dd7bf7ddde9e03667d1eb1651d5ae583c68` |
| `arena/85dbc833-logistics-work-desk-arena` | 2026-10-30T11:47:16+07:00 | 3.24 | Không | — | — | `075a7e9365a1de3841eb4f361fdd0285403b0df6` |
| `arena/8f84d03e-logistics-work-desk-arena` | 2026-10-20T14:32:24+07:00 | 13.13 | Không | — | — | `fecffa3697609158e042fce10cbd3fef28062d3d` |
| `arena/916fb9ce-logistics-work-desk-arena` | 2026-10-21T08:39:28+07:00 | 12.37 | Không | — | — | `8ed22029de49cc0953fb2024ba4dc550a49cbe51` |
| `arena/94e8df82-logistics-work-desk-arena` | 2026-11-01T22:33:56+07:00 | 0.79 | Không | — | — | `94877f725f0e33f8b5d75051a46a86cacf725d5d` |
| `arena/9b459b3f-logistics-work-desk-arena` | 2026-10-19T17:28:30+07:00 | 14.01 | Không | — | — | `27386784c1b9fdaad46e44f935353650850d5907` |
| `arena/9e611b96-logistics-work-desk-arena` | 2026-10-15T14:29:05+07:00 | 18.13 | Không | — | — | `237356f2fdc09730c60d068d4e0c87b3e4cf7a58` |
| `arena/a1cadc10-logistics-work-desk-arena` | 2026-10-30T09:46:23+07:00 | 3.33 | Không | — | — | `dd1c63d94024caeff76fef0699179c3cc38d7f6e` |
| `arena/a3117943-logistics-work-desk-arena` | 2026-10-22T22:40:35+07:00 | 10.79 | Không | [#211](https://github.com/7roger89-web/logistics-work-desk-arena/pull/211) | GIỮ: PR đang mở | `bf76ad8379039086acc73384b886e372a3c3b222` |
| `arena/a3f79889-logistics-work-desk-arena` | 2026-10-20T12:01:47+07:00 | 13.23 | Không | — | — | `11fec0ada27c939631e3a9d2322859be61dca168` |
| `arena/aa27a489-logistics-work-desk-arena` | 2026-10-17T10:55:30+07:00 | 16.28 | Không | — | — | `4b1c1019fb7f38d8b937092216a2daafca1af33c` |
| `arena/ac9a7cc5-logistics-work-desk-arena` | 2026-10-31T19:00:05+07:00 | 1.94 | Không | — | — | `10e7edc575b40943d5f3a3e650eaa3e84b4e7508` |
| `arena/ad34ce1d-logistics-work-desk-arena` | 2026-10-19T22:26:04+07:00 | 13.80 | Không | — | — | `8aba473b5208a590590e4949c589aacafbe5c01b` |
| `arena/adbc6593-logistics-work-desk-arena` | 2026-10-18T20:47:42+07:00 | 14.87 | Không | — | — | `17e49f5069b347d1c8a50a4366f25f7117fe0551` |
| `arena/ae5f9f47-logistics-work-desk-arena` | 2026-11-02T10:51:29+07:00 | 0.28 | Không | — | — | `d4c7365b3d99485321da2f40e836757535e50a01` |
| `arena/b153ecaf-logistics-work-desk-arena` | 2026-10-20T11:58:43+07:00 | 13.23 | Không | — | — | `706f7851837b2b3d5f2cd5b6e21f19098406b199` |
| `arena/bb243332-logistics-work-desk-arena` | 2026-10-15T23:54:01+07:00 | 17.74 | Không | — | — | `7ef144c22081d64806fde6e3149c4d69afd1552a` |
| `arena/bc66410c-logistics-work-desk-arena` | 2026-10-27T09:08:17+07:00 | 6.35 | Không | [#223](https://github.com/7roger89-web/logistics-work-desk-arena/pull/223) | GIỮ: PR đang mở | `35165c9e4e5a03c409d40c5f27232cd81df968b7` |
| `arena/bfa65e28-logistics-work-desk-arena` | 2026-10-31T15:42:21+07:00 | 2.08 | Không | — | — | `c0460ea826bdd54319b6ee2c3d63ea9e745fc223` |
| `arena/c78d9bf7-logistics-work-desk-arena` | 2026-10-30T20:42:23+07:00 | 2.87 | Không | — | — | `6b95af35e94ef331bdf29403d1285bd77fc8c461` |
| `arena/c8ce75e6-logistics-work-desk-arena` | 2026-11-01T21:26:09+07:00 | 0.84 | Không | — | — | `911f3174596245fc8ec4d68daef634fa07032f90` |
| `arena/ca509b81-logistics-work-desk-arena` | 2026-10-23T21:38:04+07:00 | 9.83 | Không | — | — | `423cb412f2f4207862297d73f3f0208ba38aa058` |
| `arena/cee7f2f5-logistics-work-desk-arena` | 2026-10-20T11:31:34+07:00 | 13.25 | Không | — | — | `6d544b14f578d4c31329ec2c6a40bf6a1bebe7a3` |
| `arena/cf3205ad-logistics-work-desk-arena` | 2026-10-27T08:02:55+07:00 | 6.40 | Không | [#222](https://github.com/7roger89-web/logistics-work-desk-arena/pull/222) | GIỮ: PR đang mở | `d67c94b74d1b0c62255e146d2999e2b1b7a4a24f` |
| `arena/ct-law-coldstart-83162293-20261022-logistics-work-desk-arena` | 2026-10-22T21:21:18+07:00 | 10.84 | Không | — | — | `0c5570aab88299c9749ef27c5faed9859f0d43a3` |
| `arena/ct-w4-qa-docs-sync-0c5570a-20261022` | 2026-10-22T22:40:35+07:00 | 10.79 | Không | — | — | `bf76ad8379039086acc73384b886e372a3c3b222` |
| `arena/d1d79415-logistics-work-desk-arena` | 2026-10-21T08:14:27+07:00 | 12.39 | Không | — | — | `dc02afaa3592aa231e677627c2fd90bcb6105f1f` |
| `arena/d46744d8-logistics-work-desk-arena` | 2026-10-30T14:53:44+07:00 | 3.11 | Không | — | — | `f6b8234e079f946cd0e1cc0ce427e1685ea0a6ba` |
| `arena/d657fb56-logistics-work-desk-arena` | 2026-10-16T15:58:41+07:00 | 17.07 | Không | — | — | `1fe2ff56c9214293d5318f1eb33798ddb3d81f93` |
| `arena/d8927583-logistics-work-desk-arena` | 2026-10-15T12:00:16+07:00 | 18.23 | Không | — | — | `3f42a77ea6ab490c976858323d377a6864a8da14` |
| `arena/da9aa3db-logistics-work-desk-arena` | 2026-10-19T01:01:28+07:00 | 14.69 | Không | — | — | `f51710b072eb3ab0b803331337714bb416edd26f` |
| `arena/df8f04ad-logistics-work-desk-arena` | 2026-10-22T17:13:18+07:00 | 11.02 | Không | — | — | `767eabd23aac1188770a857acaa1c645d3402e05` |
| `arena/dfd56039-logistics-work-desk-arena` | 2026-10-31T18:43:12+07:00 | 1.95 | Không | — | — | `1435bc7b3e089172be641b484f97c1554f2241c2` |
| `arena/e115abfb-logistics-work-desk-arena` | 2026-10-20T20:52:31+07:00 | 12.86 | Không | — | — | `cbe6450c424ee7a99ed26157139978c89875e6c3` |
| `arena/e3a36318-logistics-work-desk-arena` | 2026-10-30T19:13:48+07:00 | 2.93 | Không | — | — | `9b96dac0f0bba8feff89d0000102e4904e34764d` |
| `arena/e832e295-logistics-work-desk-arena` | 2026-10-21T21:39:28+07:00 | 11.83 | Không | — | — | `83162293036414dcafa01072b93eece8733b8688` |
| `arena/e9b570a0-logistics-work-desk-arena` | 2026-10-27T10:14:23+07:00 | 6.31 | Không | — | — | `07eae120f79f9e7c2d1b162de60e9b46468378e6` |
| `arena/ec138ff2-logistics-work-desk-arena` | 2026-11-02T08:39:56+07:00 | 0.37 | Không | — | — | `3b81be703d3cc3e1cf25d7c9bd9e4f317a0929df` |
| `arena/ecbac12e-logistics-work-desk-arena` | 2026-10-23T18:37:07+07:00 | 9.96 | Không | — | — | `4c4600aa52f7b24f8d1eabf9c7df4d248e9fcb52` |
| `arena/efda2efc-logistics-work-desk-arena` | 2026-10-31T09:20:24+07:00 | 2.34 | Không | — | — | `0ddc0ceddff9cfbe3d3e3ea287ee14fb224ca752` |
| `arena/f1a205f4-logistics-work-desk-arena` | 2026-10-31T16:41:36+07:00 | 2.04 | Không | — | — | `9012ee01763df491ec4d8bda9836cc3dee060aac` |
| `arena/f26588fe-logistics-work-desk-arena` | 2026-10-30T23:11:17+07:00 | 2.77 | Không | — | — | `fee72b35afb835625c0cd5fa807983520ef9fc9e` |
| `arena/f460b9a2-logistics-work-desk-arena` | 2026-10-21T10:30:06+07:00 | 12.30 | Không | — | — | `39188ab2620d7af93f6cfc4f81b3b94636dc8085` |
| `arena/fbfabbad-logistics-work-desk-arena` | 2026-10-28T07:55:53+07:00 | 5.40 | Không | — | — | `5fd29f0bc2a893a319cf23e0f8f59c3842db704a` |
| `arena/g0-prod-readonly-business-audit-20261027` | 2026-10-27T19:44:43+07:00 | 5.91 | Không | [#227](https://github.com/7roger89-web/logistics-work-desk-arena/pull/227) | GIỮ: PR đang mở | `4de17e2c61acfb47b65673f0cb8254f3541ef342` |
| `arena/g1-customer-only-entry-20261027` | 2026-10-27T14:52:27+07:00 | 6.11 | Không | — | — | `e285596fb7ef195e6d7b2eb13fb3f4eaecfe2962` |
| `arena/g1-google-root-qa-20261027` | 2026-10-27T15:18:18+07:00 | 6.10 | Không | — | — | `4eb3d127db71f810fd05a0e5eabbb985103efbab` |
| `arena/g15-approved-business-data-20261027` | 2026-10-28T18:12:30+07:00 | 4.97 | Không | [#226](https://github.com/7roger89-web/logistics-work-desk-arena/pull/226) | GIỮ: PR đang mở | `9978e0a6ee120e8de2ea4838aa2c8e23746663f9` |
| `arena/state-hygiene-2-session` | 2026-10-20T21:46:12+07:00 | 12.83 | Không | — | — | `365ad6d432b5deec421234336f2c0747138605fc` |
| `ct/browser-note-qa-gate-20261030` | 2026-10-30T23:37:33+07:00 | 2.75 | Không | [#246](https://github.com/7roger89-web/logistics-work-desk-arena/pull/246) | GIỮ: PR đang mở | `cd42e3518dd79c9e4a4585e8a5367e26846fb3e6` |
| `ct/journey-mimo-visual-fix-11e4` | 2026-10-17T11:14:25+07:00 | 16.26 | Không | — | — | `386b1c1ff58a8db8d20fc37247a42af6f8e81a91` |
| `ct/logi-app-renewal-01-t0-air-truth` | 2026-10-15T09:08:45+07:00 | 18.35 | Không | [#200](https://github.com/7roger89-web/logistics-work-desk-arena/pull/200) | GIỮ: PR đang mở | `d0a1b556187a4769f5c84ca8c0af495eec98de02` |
| `ct/logi-goal-anchor-20261030` | 2026-10-30T09:05:29+07:00 | 3.35 | Không | — | — | `156f72e3c5aa3d84d5e73325e91db39c903a1191` |
| `ct/logi-journey-discussion-20261030` | 2026-10-30T12:31:37+07:00 | 3.21 | Không | — | — | `cc9f9a7ae50abe9244ae2a457e5e3dbcb31bcc5a` |
| `ct/logi-next-browser-graphify-20261030` | 2026-10-30T20:56:47+07:00 | 2.86 | Không | [#242](https://github.com/7roger89-web/logistics-work-desk-arena/pull/242) | GIỮ: PR đang mở | `a740afb0351574da28620985b18b7649dd57adea` |
| `ct/logi197-journey-operator-clarity` | 2026-10-14T09:20:46+07:00 | 19.34 | Không | [#198](https://github.com/7roger89-web/logistics-work-desk-arena/pull/198) | GIỮ: PR đang mở | `eae19e3c26375396f05993a9c63d25d8fcaade61` |
| `ct/logi199-int198-preview` | 2026-10-15T11:11:01+07:00 | 18.27 | Không | — | — | `d96d95125b41b97078d42278a7e1fee30d3bf7b7` |
| `ct/logi199-journey-main-integration-20261017` | 2026-10-18T21:22:09+07:00 | 14.84 | Không | [#210](https://github.com/7roger89-web/logistics-work-desk-arena/pull/210) | GIỮ: PR đang mở | `408b98002b6e002859fc5217d5e57cf202ec5ee9` |
| `ct/logi199-owner-oracle-paper-20261016` | 2026-10-15T23:54:01+07:00 | 17.74 | Không | — | — | `7ef144c22081d64806fde6e3149c4d69afd1552a` |
| `ct/logi199-owner-visual-fidelity-v2` | 2026-10-15T12:39:58+07:00 | 18.21 | Không | — | — | `2b8fb676025c8dbf6718cc3f7a0817aa23aee718` |
| `ct/logi199-t1-fcl-lifecycle-truth` | 2026-10-15T09:57:29+07:00 | 18.32 | Không | [#202](https://github.com/7roger89-web/logistics-work-desk-arena/pull/202) | GIỮ: PR đang mở | `198c7b43202193e21a40ab0d3dd17b88e180c13d` |
| `ct/logi199-t1-fcl-multi-container-truth` | 2026-10-15T09:18:44+07:00 | 18.35 | Không | [#201](https://github.com/7roger89-web/logistics-work-desk-arena/pull/201) | GIỮ: PR đang mở | `d6f1e2dfc45abb92034bd987486d758720d3d551` |
| `ct/logi199-t2-t4-mode-truth` | 2026-10-15T10:08:14+07:00 | 18.31 | Không | [#203](https://github.com/7roger89-web/logistics-work-desk-arena/pull/203) | GIỮ: PR đang mở | `db9da298a191be212ac0d7aefba67fbf4d879016` |
| `ct/logi199-t5-app-identity` | 2026-10-15T11:10:18+07:00 | 18.27 | Không | [#204](https://github.com/7roger89-web/logistics-work-desk-arena/pull/204) | GIỮ: PR đang mở | `c53437e736ab861b41cd063af08142aae0d91311` |
| `ct/logi199-t6-integration` | 2026-10-15T11:16:00+07:00 | 18.26 | Không | — | — | `75097da1f85b0500fd96090fd01cd5a234bb3fd3` |
| `docs/log-owner-intent-gate-20261030` | 2026-10-30T17:09:13+07:00 | 3.02 | Không | — | — | `6a0aebd55188831127b974e938701e7350128a7b` |
| `experiments/agent-tools-20261030` | 2026-10-30T18:19:01+07:00 | 2.97 | Không | — | — | `408d81cd3e7ce2e530faf0a37a8bd15c69865c21` |
| `experiments/code-browser-tool-probe-20261030` | 2026-10-30T20:12:31+07:00 | 2.89 | Không | — | — | `5c99c39be0d8ae5a694ac52c7e95751012f25767` |
| `experiments/graphify-pilot-20261030` | 2026-10-30T17:36:22+07:00 | 3.00 | Không | — | — | `59b3ce1786c44cdd2cce49a3bd8d8ed2d3cdd46e` |
| `experiments/pr243-independent-acceptance-20261030` | 2026-10-30T20:51:57+07:00 | 2.86 | Không | — | — | `1c2f53f3bb3afa6b7d05fec3942d3415d1057023` |
| `experiments/test-impact-20261030` | 2026-10-30T22:04:56+07:00 | 2.81 | Không | — | — | `0ee1215b2731293232b6e63f13706bd6c04782a4` |
| `experiments/test-impact-nocache-20261030` | 2026-10-30T22:07:41+07:00 | 2.81 | Không | — | — | `8b7e01aebac1290a2c4e4d5921584f24974ba3de` |
| `fix/176-journey-demo-fidelity-20261004` | 2026-10-04T22:18:11+07:00 | 28.80 | Không | [#177](https://github.com/7roger89-web/logistics-work-desk-arena/pull/177) | GIỮ: PR đang mở | `70fd3610fdf9e2dacc7c5f7ac65440ad52e0ced7` |
| `fix/journey-discussion-readable-20261030` | 2026-10-30T17:54:27+07:00 | 2.99 | Không | — | — | `464129cbd274f43838af3d00e2cef1df7c32fca8` |
| `hexa/tt-lg-publication-v0-20261022` | 2026-10-22T17:51:45+07:00 | 10.99 | Không | — | — | `4cd1ca7a2a3389576818d8be6320f1989e6b4e97` |
| `process/logi-execution-acceptance-20261031` | 2026-10-31T09:10:08+07:00 | 2.35 | Không | — | — | `e395c570774396e27cef366023d4f2ccb6a77041` |
| `task/agents-process-rewrite` | 2026-11-02T17:32:28+07:00 | 0.00 | Không | [#257](https://github.com/7roger89-web/logistics-work-desk-arena/pull/257) | GIỮ: PR đang mở | `124ea1346b4b8b18bb0d0a7ba959a57321cda0b7` |

## CHƯA GỘP trên 30 ngày

| Nhánh remote | Commit cuối (UTC+07:00) | Tuổi (ngày) | Đã gộp main / bằng chứng | PR đang mở | Bảo vệ | Head SHA |
|---|---|---:|---|---|---|---|
| `arena/01a0f53f-logistics-work-desk-arena` | 2026-10-01T09:43:50+07:00 | 32.33 | Không | — | — | `45a0689988a4928960daa7fda5e83c5dc0d350c5` |
| `arena/01a0ffef-logistics-work-desk-arena` | 2026-10-03T11:32:11+07:00 | 30.25 | Không | [#174](https://github.com/7roger89-web/logistics-work-desk-arena/pull/174) | GIỮ: PR đang mở | `d41a13b88fcddf752a32ca2bf444fe641c5a8bdd` |
| `arena/logi-delivery-note-xlsx-156` | 2026-10-01T13:55:30+07:00 | 32.15 | Không | [#157](https://github.com/7roger89-web/logistics-work-desk-arena/pull/157) | GIỮ: PR đang mở | `f4fa4c6a4e5f7838d5cf35e00e5057bbd078e673` |
| `arena/logi-gemini-ocr-01` | 2026-09-24T16:59:14+07:00 | 39.03 | Không | [#111](https://github.com/7roger89-web/logistics-work-desk-arena/pull/111) | GIỮ: PR đang mở | `cc71996e3a7fb6c5a006102b2d822c21782cef40` |
| `build/notebooklm-dist-20260930` | 2026-09-30T10:27:13+07:00 | 33.30 | Không | — | — | `b39f97b4d50912f24f370dcd50bc10a8601ba48d` |
| `ct/attention-166-fresh` | 2026-10-02T16:52:49+07:00 | 31.03 | Không | — | — | `02af685b209e54a275c282f38f7391a3fc11703a` |
| `ct/issue-166-support-attention-now-impl` | 2026-10-02T16:48:01+07:00 | 31.03 | Không | — | — | `3cc6cadebac6b53073c986b740f67b00cab804b4` |
| `ct/support-attention-now-v1` | 2026-10-02T15:01:36+07:00 | 31.11 | Không | — | — | `81a250c4df8ed5cf1a0823b420ec57f622aaadc5` |
| `ct/visual-shipment-workspace-reference` | 2026-10-01T21:54:59+07:00 | 31.82 | Không | — | — | `701f1a9384e54b5d3df9ab046d226bf83cb74b0c` |
| `ct/work-module-library-v1` | 2026-10-02T07:29:15+07:00 | 31.42 | Không | — | — | `bc0861ec8fd7262509dacf45fbb336be26876b79` |
| `owner-input/form07-source-168` | 2026-10-03T08:54:29+07:00 | 30.36 | Không | — | — | `51eaaed93cadbc4772959866dce04cf35ffd3e43` |
| `p2p/issue-296-portable-law-sync` | 2026-10-02T22:22:25+07:00 | 30.80 | Không | — | — | `6ba4a3a92eb4d96a8f427995b16631dc53103d4b` |

## Điểm dừng

Đã ghi đủ nhánh, ngày commit, bằng chứng gộp và ba nhóm. Không có lệnh xoá nào được chạy. Không cài skill. Chờ Owner xem báo cáo và nói tiếp trước phần B.
