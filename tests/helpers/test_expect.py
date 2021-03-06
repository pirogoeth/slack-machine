# -*- coding: utf-8 -*-

import asyncio
import time
from inspect import isawaitable, iscoroutinefunction
from unittest.mock import call

import pytest

from tests.helpers.expect import (
    ExpectMagicMock,
    ExpectMock,
    ExpectMockFixture,
    Expectation,
    NoExpectationForCall,
    UnusedCallsError,
    expect,
    patch,
)


def test_basic_expectation():
    mock = ExpectMock()
    mock.expect("a").returns(1).returns(2)
    mock.expect("b").returns(3).returns(4)
    mock.expect("c").raises(Exception("C")).returns(5)

    assert mock("a") == 1
    assert mock("a") == 2
    with pytest.raises(NoExpectationForCall):
        mock("a")

    assert mock("b") == 3
    assert mock("b") == 4
    with pytest.raises(NoExpectationForCall):
        mock("b")

    with pytest.raises(Exception):
        mock("c")
    assert mock("c") == 5
    with pytest.raises(NoExpectationForCall):
        mock("c")


def test_call_record():
    mock = ExpectMock()
    mock.expect("a").returns(1).returns(2)

    assert mock("a") == 1
    mock.assert_has_calls([call("a")])

    assert mock("a") == 2
    mock.assert_has_calls([call("a"), call("a")])


def test_magic_child_instance():
    mock = ExpectMagicMock()
    assert isinstance(mock.some_function, ExpectMagicMock)
    assert isinstance(mock.__len__, ExpectMagicMock)


def test_patch():
    with patch("time.sleep", new_callable=ExpectMock) as sleep:
        sleep.expect(1).returns(True)
        assert time.sleep(1) == True


def test_always():
    mock = ExpectMagicMock()
    mock.expect("a").returns(1, always=True)
    mock.expect("b").returns(2, always=False)
    assert mock("a") == 1
    assert mock("b") == 2
    assert mock("a") == 1
    with pytest.raises(NoExpectationForCall):
        mock("b")


def test_expect_fixture(expect: ExpectMockFixture):
    assert isinstance(expect, ExpectMockFixture)
    sleep = expect.patch("time.sleep")
    sleep.expect(1).returns(True)
    assert time.sleep(1) == True

    expect.stop_all()
    assert time.sleep(0.1) == None


@pytest.mark.xfail(raises=UnusedCallsError, strict=True)
def test_raises_for_unused_calls(expect: ExpectMockFixture):
    sleep = expect.patch("time.sleep")
    sleep.expect(0.5).returns(True)
    sleep.expect(1).returns(True)
    assert time.sleep(0.5)
    expect.check_for_unused_mock_calls()


def test_ignore_unused_calls(expect: ExpectMockFixture):
    sleep = expect.patch("time.sleep", ignore_unused_calls=True)
    sleep.expect(0.5).returns(True)
    sleep.expect(1).returns(True)
    assert time.sleep(0.5)
    expect.check_for_unused_mock_calls()


@pytest.mark.asyncio
async def test_expect_asyncio(expect: ExpectMockFixture):
    sleep = expect.patch_async("asyncio.sleep")
    sleep.expect(1).returns(True)
    assert asyncio.iscoroutinefunction(asyncio.sleep)
    awaitable = asyncio.sleep(1)
    assert isawaitable(awaitable)
    assert (await awaitable) == True
    expect.check_for_unused_mock_calls()


def test_wildcard_calls(expect: ExpectMockFixture):
    somefn = ExpectMock()
    somefn.expect("a", ..., "c").returns(1)
    somefn.expect(..., "b", "d").returns(2)

    assert somefn("a", 3, "c") == 1
    assert somefn(1, "b", "d") == 2
    expect.check_for_unused_mock_calls()


def test_wildcard_calls_always(expect: ExpectMockFixture):
    sleep = expect.patch("time.sleep")
    sleep.expect(...).returns(15, always=True)

    assert time.sleep(1) == 15
    assert time.sleep(15) == 15
    expect.check_for_unused_mock_calls()


@pytest.mark.asyncio
async def test_async_mock_drill(expect: ExpectMockFixture):
    item = expect.AsyncExpectMock()
    item.otherthing.function.expect("a", "b").returns(10)

    with pytest.raises(NoExpectationForCall):
        await item.otherthing.function("b", "c")

    assert (await item.otherthing.function("a", "b")) == 10
