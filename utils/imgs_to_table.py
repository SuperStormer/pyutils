def imgs_to_table(imgs, column_num):
	"""imgs is (caption,image url) list. returns html table in string form """
	result = """<style>
	table {
		border-collapse: collapse;
	}
	td {
		border: 2px solid black;
	}
</style>
<table>"""
	for i, (caption, url) in enumerate(imgs):
		if i % column_num == 0:
			result += "<tr>"
		result += f"<td>{caption}<br><img src=\"{url}\"></td>"
		if i % column_num == column_num - 1:
			result += "</tr>"
	result += "</table>"
	return result
