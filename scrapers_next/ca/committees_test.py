from spatula import HtmlListPage, URL, XPath, CSS, HtmlPage, SelectorError
from openstates.models import ScrapeCommittee
import re


class ChooseType(HtmlPage):
    def process_page(self):

        xpaths = {
            "type_one": "//div/p/a[(contains(text(), 'Senator') or contains(text(), 'Assembly Member'))]/text()",
            "type_two": "//a[(contains(@href, '/sd') or "
            "contains(@href, 'assembly.ca.gov/a')) and "
            "(starts-with(text(), 'Senator') or "
            "starts-with(text(), 'Assembly Member'))]/text()",
            "type_three": '//tbody/tr/td/a[(contains(@href, "/sd") or '
            'contains(@href, "assembly.ca.gov/a"))]/text()',
            "type_four": "//p[@class = 'caption']/text()",
        }

        for page_type, xpath in xpaths.items():
            try:
                XPath(xpath).match(self.root)
                break
            except SelectorError:
                continue

        if page_type == "type_one":
            # return None
            return Type_One(self.input, source=self.source)
        elif page_type == "type_two":
            # return None
            return Type_Two(self.input, source=self.source)
        elif page_type == "type_three":
            # return None
            return Type_Three(self.input, source=self.source)
        else:
            return Type_Four(self.input, source=self.source)


class Type_One(HtmlPage):
    """
    Type One pages are usually formatted with a red background.
    The format is: Senator Name (role)
    """

    def process_page(self):
        com = self.input
        members = XPath(
            "//div/p/a[(contains(text(), 'Senator') or contains(text(), 'Assembly Member'))]/text()"
        ).match(self.root)

        for member in members:
            member = re.sub(r"(Senator\s|Assembly\sMember\s)", "", member)

            if re.search(r"\((D|R)\)", member):
                mem_name, _ = member.split("(")
                print(mem_name)
                if re.search(r",\s", mem_name):
                    mem_role, mem_name = member.split(",")
                else:
                    mem_role = "member"
                print(mem_role)
            elif re.search(r",\s", member):
                mem_name, mem_role = member.split(",")
                # print(mem_role)
                # print(mem_name)
                # mem_name, _ = mem_name.split("(")
            elif re.search(r"\(", member):
                mem_name, mem_role = member.split("(")
                mem_role = mem_role.rstrip(")")
            else:
                mem_name = member
                mem_role = "member"

            print(mem_name, mem_role)
            com.add_member(mem_name, role=mem_role)

        return com


class Type_Two(HtmlPage):
    """ """

    def process_page(self):
        com = self.input
        members = XPath(
            "//a[(contains(@href, '/sd') or "
            "contains(@href, 'assembly.ca.gov/a')) and "
            "(starts-with(text(), 'Senator') or "
            "starts-with(text(), 'Assembly Member'))]/text()"
        ).match(self.root)
        # print(item)

        for member in members:
            (mem_name, mem_role) = re.search(
                r"""(?ux)
                    ^(?:Senator|Assembly\sMember)\s  # Legislator title
                    (.+?)  # Capture the senator's full name
                    (?:\s\((.{2,}?)\))?  # There may be role in parentheses
                    (?:\s\([RD]\))?  # There may be a party affiliation
                    \s*$
                    """,
                member,
            ).groups()

            print(mem_name, mem_role)
            com.add_member(mem_name, role=mem_role if mem_role else "member")

        return com


class Type_Three(HtmlPage):
    """
    Type Three pages are usually formatted with a green background.
    The format is: Name (role)
    """

    def process_page(self):
        com = self.input
        members = XPath(
            "//tbody/tr/td/a[(contains(@href, '/sd') or contains(@href, 'assembly.ca.gov/a'))]/text()"
        ).match(self.root)
        # print(item)

        for member in members:
            (mem_name, mem_role) = re.search(
                r"""(?ux)
                    (.+?)  # Capture the senator's full name
                    (?:\s\((.{2,}?)\))?  # There may be role in parentheses
                    \s*$
                    """,
                member,
            ).groups()
            print(mem_name, mem_role)
            com.add_member(mem_name, role=mem_role if mem_role else "member")

        return com


class Type_Four(HtmlPage):
    """
    Type Three pages are usually formatted with a green background.
    The format is: Name, role where role is on a new line
    """

    def process_page(self):
        com = self.input

        try:
            members = CSS("div.chair img").match(self.root)
        except SelectorError:
            members = [CSS("p img").match(self.root)[0]]
        # print(members)
        mem_num = 0
        for member in members:
            mem = member.get("alt")
            # print(mem)
            if not mem or re.search(r"Assemblymember", mem):
                mem = member.getnext().text_content()
                # print(mem)

            mem = re.sub(r"(Senator\s|Assembly\sMember\s)", "", mem)
            mem = re.sub(r"Image\sof\s", "", mem)
            # print(mem)
            if re.search(r",\s(V|C|\()", mem):
                # x = re.split(r",\s(V|C|\()", mem)
                # print(x)
                # mem_name, mem_role = re.split(r",\s(V|C|\()", mem)
                mem_name, mem_role = mem.split(",")
                mem_name = mem_name.strip()
                mem_role = mem_role.strip()
                if "(" in mem_role:
                    mem_role = mem_role.lstrip("(").rstrip(")")
                if "of the" in mem_role:
                    mem_role = mem_role.split("of the")[0].strip()
                if mem_name == "Kevin Kiley":
                    mem_role = "Vice Chair"
                # print(mem_name, mem_role)
            elif re.search(r"\s\((V|C)", mem):
                mem_name, mem_role = mem.split("(")
                mem_name = mem_name.strip()
                mem_role = mem_role.rstrip(")").strip()
                # print(mem_name, mem_role)
            elif re.search(r"\n", mem):
                mem_name, mem_role = mem.split("\n")
                mem_name = mem_name.strip()
                mem_role = mem_role.strip().split("of the")[0].strip()
            elif mem_num == 0:
                mem_name = mem.strip()
                mem_role = "Chair"
                # print(member, "chair not listed")
            else:
                mem_name = mem.strip()
                mem_role = "Vice Chair"
                # print(member, "vice chair not listed")
            mem_num += 1

            print(mem_name, mem_role)
            com.add_member(mem_name, role=mem_role if mem_role else "member")

        return com


class SenateCommitteeList(HtmlListPage):
    source = URL("http://senate.ca.gov/committees")

    selector = XPath("//h2/../following-sibling::div//a")

    def process_item(self, item):
        comm_name = XPath("text()").match_one(item)
        if comm_name in ["Teleconference How-To Information", "Legislative Process"]:
            self.skip()

        comm_url = XPath("@href").match_one(item)

        if comm_name.startswith("Joint"):
            # self.skip()
            com = ScrapeCommittee(
                name=comm_name, classification="committee", parent="legislature"
            )
        elif comm_name.startswith("Subcommittee"):
            com = ScrapeCommittee(
                name=comm_name, classification="subcommittee", parent=""
            )
        else:
            com = ScrapeCommittee(
                name=comm_name, classification="committee", parent="upper"
            )
        com.add_source(self.source.url)
        com.add_source(comm_url)
        com.add_link(comm_url, note="homepage")
        return ChooseType(com, source=URL(comm_url))
