import pytest
from assembler.chip8 import tokenize, assemble


class TestTokenize:
    _test_single_line = [
        ("single_token", "RET", ["RET"]),
        ("two_tokens_space", "JMP main", ["JMP", "main"]),
        ("two_tokens_spaces", "JMP   0x200", ["JMP", "0x200"]),
        ("comment_hash_only", "#comment", []),
        ("comment_hash_no_space", "CLS#comment", ["CLS"]),
        ("comment_hash_after_space", "CLS # comment", ["CLS"]),
        ("comment_semi_only", ";comment", []),
        ("comment_semi_no_space", "CLS;comment", ["CLS"]),
        ("comment_semi_after_space", "CLS ; comment", ["CLS"]),
        ("delimiter_no_spaces", "ADD V1,V2", ["ADD", "V1", ",", "V2"]),
        ("delimiter_space_after", "ADD V1, V2", ["ADD", "V1", ",", "V2"]),
        ("delimiter_space_before", "ADD V1 ,V2", ["ADD", "V1", ",", "V2"]),
        ("delimiter_surround_spaces", "ADD V1 , V2", ["ADD", "V1", ",", "V2"]),
        ("delimiter_repeated", "ADD V1,,V2", ["ADD", "V1", ",", ",", "V2"]),
        ("label_no_space", "main:", ["main", ":"]),
        ("label_after_space", "main :", ["main", ":"]),
    ]

    @pytest.mark.parametrize(
        "test_id, line, expected",
        _test_single_line,
        ids=[t[0] for t in _test_single_line]
    )
    def test_single_line(self, test_id, line, expected):
        assert tokenize(line) == expected


class TestAssemble:
    _test_single_line = [
        # empty / comment
        (" ", ""),
        ("\t", ""),
        ("# comment", ""),
        ("; comment", ""),
        # standard instructions
        ("CLS", "00E0"),
        ("RET", "00EE"),
        # test SYS with various number specifications
        ("SYS E0h", "00E0"),
        ("SYS 777o", "01FF"),
        ("SYS 111100001111b", "0F0F"),
        ("SYS 0x3E0", "03E0"),
        ("SYS 255", "00FF"),
        ("SYS 0o555", "016D"),
        ("SYS 0b101010101010", "0AAA"),
        # test JP with various offset specifications
        ("JP $", "1200"),
        ("JP $+A20h", "1C20"),
        ("JP $-0o700", "1040"),
        # continue standard instructions
        ("HLT", "1200"),  # alternative to 'JP $'
        ("JP AAAh", "1AAA"),
        ("CALL 555h", "2555"),
        ("SE V1, 127", "317F"),
        ("SNE V1, 127", "417F"),
        ("SE VA, V5", "5A50"),
        ("LD V5, 255", "65FF"),
        ("ADD V6, 255", "76FF"),
        ("LD V5, V6", "8560"),
        ("OR V5, V6", "8561"),
        ("AND V5, V6", "8562"),
        ("XOR V5, V6", "8563"),
        ("ADD V5, V6", "8564"),
        ("SUB V5, V6", "8565"),
        ("SHR V5, V6", "8566"),
        ("SHR V7", "8776"),
        ("SUBN V5, V6", "8567"),
        ("SHL V5, V6", "856E"),
        ("SHL V7", "877E"),
        ("SHL V5, V6", "856E"),
        ("SNE V5, V6", "9560"),
        ("LD I, BCDh", "ABCD"),
        ("JP V0, CDEh", "BCDE"),
        ("RND V3, ABh", "C3AB"),
        ("DRW V1, V2, 4", "D124"),
        # todo 0xE***, 0xF***
        # constants
        ("DW FEDCh", "FEDC"),
    ]

    @pytest.mark.parametrize(
        "line, expected",
        _test_single_line,
        ids=[t[0] for t in _test_single_line]
    )
    def test_single_line(self, line, expected):
        assert assemble([line]).encode("hex").upper() == expected

    def test_jump_label(self):
        assert assemble(["main:", " ", "JP main"]) == "\x12\x00"
