from django.core.management.base import BaseCommand
import xmltodict
import os
from api.utils import pickle_
from wikiwho.wikiwho_simple import Wikiwho

# this is taken from examples.Finger_Lakes3.xml
x = """
<page>
    <title>Finger Lakes</title>
    <ns>0</ns>
    <id>33333</id>
    <revision>
      <id>0</id>
      <timestamp>2002-12-29T00:45:46Z</timestamp>
      <contributor>
       <username>Editor A</username>
        <id>111</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There is a house on a hill .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>1</id>
      <timestamp>2002-12-29T00:45:47Z</timestamp>
      <contributor>
       <username>Editor B</username>
        <id>222</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the hill . A tree was standing close !</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>2</id>
      <timestamp>2002-12-29T00:45:48Z</timestamp>
      <contributor>
       <username>Editor C</username>
        <id>333</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the hill .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>3</id>
      <timestamp>2002-12-29T00:45:49Z</timestamp>
      <contributor>
       <username>Editor D</username>
        <id>444</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the hill . A tree was standing close !</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>4</id>
      <timestamp>2002-12-29T00:45:50Z</timestamp>
      <contributor>
       <username>Editor C</username>
        <id>333</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the hill . A tree was standing nearby .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
    <revision>
      <id>5</id>
      <timestamp>2002-12-29T00:45:51Z</timestamp>
      <contributor>
       <username>Editor G</username>
        <id>555</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was some hut on the hill . A tree was standing nearby .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>6</id>
      <timestamp>2002-12-29T00:45:52Z</timestamp>
      <contributor>
       <username>Editor J</username>
        <id>666</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the hill . A tree was standing nearby .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>7</id>
      <timestamp>2002-12-29T00:45:53Z</timestamp>
      <contributor>
       <username>Editor D</username>
        <id>444</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the hill . A tree was standing nearby . No grass has been seen around</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>8</id>
      <timestamp>2002-12-29T00:45:54Z</timestamp>
      <contributor>
       <username>Editor E</username>
        <id>777</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the hill . A tree was standing nearby . No grass was there</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>9</id>
      <timestamp>2002-12-29T00:45:55Z</timestamp>
      <contributor>
       <username>Editor C</username>
        <id>333</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the hill . A tree was standing nearby . No grass was growing there</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>10</id>
      <timestamp>2002-12-29T00:45:56Z</timestamp>
      <contributor>
       <username>Editor F</username>
        <id>888</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the hill . A tree was standing nearby . No grass was growing there .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>11</id>
      <timestamp>2002-12-29T00:45:57Z</timestamp>
      <contributor>
       <username>Editor V1</username>
        <id>999</id>
      </contributor>
      <text xml:space="preserve" bytes="515">kirby kirby kirby kirby kirby</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>12</id>
      <timestamp>2002-12-29T00:45:58Z</timestamp>
      <contributor>
       <username>Editor A</username>
        <id>111</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the hill . A tree was standing nearby . No grass was growing there .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>13</id>
      <timestamp>2002-12-29T00:45:59Z</timestamp>
      <contributor>
       <username>Editor V2</username>
        <id>101010</id>
      </contributor>
      <text xml:space="preserve" bytes="515">penguins are fantastic magicians but noone knows it ! No grass was growing there .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>14</id>
      <timestamp>2002-12-29T00:46:46Z</timestamp>
      <contributor>
       <username>Editor V1</username>
        <id>999</id>
      </contributor>
      <text xml:space="preserve" bytes="515">lalalalala lalala</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>15</id>
      <timestamp>2002-12-29T00:47:46Z</timestamp>
      <contributor>
       <username>Editor B</username>
        <id>222</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the hill . A tree was standing nearby . No grass was growing there .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>16</id>
      <timestamp>2002-12-29T00:48:46Z</timestamp>
      <contributor>
       <username>Editor V1</username>
        <id>999</id>
      </contributor>
      <text xml:space="preserve" bytes="515">lalalalala lalala</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>17</id>
      <timestamp>2002-12-29T00:49:46Z</timestamp>
      <contributor>
       <username>Editor B</username>
        <id>222</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the hill . A tree was standing nearby . No grass was growing there .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>18</id>
      <timestamp>2002-12-29T00:50:46Z</timestamp>
      <contributor>
       <username>Editor V3</username>
        <id>111111</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a freasdas on the hill . A umu was standing nearby . No musuluaophdhp was growing there .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>19</id>
      <timestamp>2002-12-29T00:51:46Z</timestamp>
      <contributor>
       <username>Editor A</username>
        <id>111</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the hill . A tree was standing nearby . No grass was growing there .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>20</id>
      <timestamp>2002-12-29T00:52:46Z</timestamp>
      <contributor>
       <username>Editor V3</username>
        <id>111111</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house  the hill . A tree was standing nearby . No grass  growing there .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>21</id>
      <timestamp>2002-12-29T00:53:46Z</timestamp>
      <contributor>
       <username>Editor J</username>
        <id>666</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the hill . A tree was standing nearby . No grass  growing there .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>22</id>
      <timestamp>2002-12-29T00:54:46Z</timestamp>
      <contributor>
       <username>Editor B</username>
        <id>222</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the hill . A tree was standing nearby . No grass was growing there .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>23</id>
      <timestamp>2002-12-29T00:55:46Z</timestamp>
      <contributor>
       <username>Editor F</username>
        <id>888</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the hill . A tree was standing nearby . No grass was growing there . Formerly , chickens were even living  here .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>24</id>
      <timestamp>2002-12-29T00:56:46Z</timestamp>
      <contributor>
       <username>Editor H</username>
        <id>121212</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the hill . A tree was standing nearby . No grass was growing there .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>25</id>
      <timestamp>2002-12-29T00:57:46Z</timestamp>
      <contributor>
       <username>Editor A</username>
        <id>111</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the hill . A tree was standing in close vicinity . No grass was growing there .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>26</id>
      <timestamp>2002-12-29T00:58:46Z</timestamp>
      <contributor>
       <username>Editor H</username>
        <id>121212</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the small hill . A tree was standing in close vicinity . No grass was growing there .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
     <revision>
      <id>27</id>
      <timestamp>2002-12-29T00:59:46Z</timestamp>
      <contributor>
       <username>Editor J</username>
        <id>666</id>
      </contributor>
      <text xml:space="preserve" bytes="515">There was a house on the small hill . A tree was standing in close vicinity . No grass was growing there yet .</text>
      <sha1>41jrbn2gk1afb385claavn1ua31dadv</sha1>
      <model>wikitext</model>
      <format>text/x-wiki</format>
    </revision>
</page>
"""


def xml_to_pickle(output_path):
    article_name = ''
    pickle_name = ''
    revisions = []
    o = xmltodict.parse(x)
    for _, data in o.items():
        for key, value in data.items():
            if key == 'title':
                article_name = value.replace(" ", "_")
                pickle_name = article_name.replace("/", "0x2f")
                print(value)
            elif key == 'revision':
                for revision in value:
                    # print(revision['id'])
                    # print(revision['timestamp'])
                    # print(revision['contributor']['username'])
                    # print(revision['contributor']['id'])
                    # print(revision['text']['#text'])
                    # print(revision['sha1'])
                    rev = {
                        '*': revision['text']['#text'],
                        'sha1': '',
                        'comment': '',
                        'revid': revision['id'],
                        'timestamp': revision['timestamp'],
                        'userid': revision['contributor']['id'],
                        'user': revision['contributor']['username'],
                    }
                    revisions.append(rev)
                    # print(rev)
                if article_name:
                    wikiwho = Wikiwho(article_name)
                    wikiwho.page_id = 111
                    wikiwho.analyse_article(revisions)
                    wikiwho._clean()
    if pickle_name:
        pickle_path = '{}/{}.p'.format(output_path, pickle_name)
        pickle_(wikiwho, pickle_path)


class Command(BaseCommand):
    help = "Create pickle for Finger Lakes xml."

    def add_arguments(self, parser):
        parser.add_argument('-o', '--output', help='Output folder path for log', required=True)

    def handle(self, *args, **options):
        output_path = options['output']
        xml_to_pickle(output_path)