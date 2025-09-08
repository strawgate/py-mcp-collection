from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import ClassVar, Generic, Literal, Self, override

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import TypeVar


class BaseQualifier(BaseModel, ABC, frozen=True):
    """The `BaseQualifier` operator is the base class for all qualifiers."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    @abstractmethod
    def to_query(self, nested: bool = False) -> str: ...

    """Render the qualifier to a query string.

    Args:
        nested: Whether the qualifier is nested and thus should be wrapped in parentheses.

    Returns:
        The query string.
    """


class AssigneeQualifier(BaseQualifier, frozen=True):
    assignee: str = Field(description="The assignee to search for.")

    def to_query(self, nested: bool = False) -> str:  # noqa: ARG002
        return f'assignee:"{self.assignee}"'


class AuthorQualifier(BaseQualifier, frozen=True):
    author: str = Field(description="The author to search for.")

    def to_query(self, nested: bool = False) -> str:  # noqa: ARG002
        return f'author:"{self.author}"'


class IssueOrPullRequestQualifier(BaseQualifier, frozen=True):
    issue_or_pull_request: Literal["issue", "pr"] = Field(
        description="The search statement is for an issue or pull request, i.e. 'issue', 'pr'."
    )

    def to_query(self, nested: bool = False) -> str:  # noqa: ARG002
        return f"is:{self.issue_or_pull_request}"


class IssueTypeQualifier(BaseQualifier, frozen=True):
    type: str = Field(description="The type to search for, i.e. 'bug', 'feature', etc.")

    def to_query(self, nested: bool = False) -> str:  # noqa: ARG002
        return f'type:"{self.type}"'


class KeywordQualifier(BaseQualifier, frozen=True):
    keyword: str = Field(description="The keyword to search for.")

    def to_query(self, nested: bool = False) -> str:  # noqa: ARG002
        # escape backslashes with more backslashes
        keyword = self.keyword.replace("\\", "\\\\")

        # escape quotes with backslashes
        keyword = keyword.replace('"', '\\"')

        return f'"{keyword}"'


class AllKeywordsQualifier(BaseQualifier, frozen=True):
    keywords: set[str] = Field(description="The keywords to search for.")

    def to_query(self, nested: bool = False) -> str:  # noqa: ARG002
        sorted_keywords = sorted(self.keywords)
        return " AND ".join([f'"{keyword}"' for keyword in sorted_keywords])


class AnyKeywordsQualifier(BaseQualifier, frozen=True):
    keywords: set[str] = Field(description="The keywords to search for.")

    def to_query(self, nested: bool = False) -> str:  # noqa: ARG002
        sorted_keywords = sorted(self.keywords)
        return " OR ".join([f'"{keyword}"' for keyword in sorted_keywords])


class KeywordInQualifier(BaseQualifier, frozen=True):
    location: Literal["title", "body", "comments"] = Field(
        description="The location to search for keywords in, i.e. 'title', 'body', 'comments'."
    )

    def to_query(self, nested: bool = False) -> str:  # noqa: ARG002
        return f"in:{self.location}"


class LabelQualifier(BaseQualifier, frozen=True):
    label: str = Field(description="The label to search for.")

    def to_query(self, nested: bool = False) -> str:  # noqa: ARG002
        return f'label:"{self.label}"'


class OwnerQualifier(BaseQualifier, frozen=True):
    owner: str = Field(description="The owner or organization to search for.")

    def to_query(self, nested: bool = False) -> str:  # noqa: ARG002
        return f'owner:"{self.owner}"'


class RepoQualifier(BaseQualifier, frozen=True):
    owner: str = Field(description="The owner or organization to search for.")
    repo: str = Field(description="The repository to search for under the owner.")

    def to_query(self, nested: bool = False) -> str:  # noqa: ARG002
        return f'repo:"{self.owner}/{self.repo}"'


class StateQualifier(BaseQualifier, frozen=True):
    state: Literal["open", "closed"] = Field(description="The state to search for, i.e. 'open', 'closed'.")

    def to_query(self, nested: bool = False) -> str:  # noqa: ARG002
        return f"state:{self.state}"


AllQualifierTypes = (
    AssigneeQualifier
    | AuthorQualifier
    | IssueOrPullRequestQualifier
    | IssueTypeQualifier
    | KeywordQualifier
    | AllKeywordsQualifier
    | AnyKeywordsQualifier
    | KeywordInQualifier
    | LabelQualifier
    | OwnerQualifier
    | RepoQualifier
    | StateQualifier
)

QualifierTypes = TypeVar("QualifierTypes", bound=BaseQualifier, default=AllQualifierTypes)
AdvancedQualifierTypes = TypeVar("AdvancedQualifierTypes", bound=BaseQualifier, default=AllQualifierTypes)


class BaseOperator(BaseModel, ABC, Generic[QualifierTypes]):
    """The `BaseOperator` operator is the base class for all operators."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    clauses: Sequence["QualifierTypes | BaseOperator[QualifierTypes]"] = Field(description="The clauses of the operator.")

    @abstractmethod
    def to_query(self, nested: bool = False) -> str: ...

    """Render the operator to a query string.

    Args:
        nested: Whether the operator is nested and thus should be wrapped in parentheses.

    Returns:
        The query string.
    """

    def add_clause(self, clause: "QualifierTypes | BaseOperator[QualifierTypes] | None") -> Self:
        if clause is None:
            return self

        self.clauses = [*self.clauses, clause]

        return self


class OrOperator(BaseOperator[QualifierTypes], BaseModel, Generic[QualifierTypes]):
    @override
    def to_query(self, nested: bool = False) -> str:
        query = " OR ".join([clause.to_query(nested=True) for clause in self.clauses])
        return "(" + query + ")" if nested else query


class AndOperator(BaseOperator[QualifierTypes], BaseModel, Generic[QualifierTypes]):
    @override
    def to_query(self, nested: bool = False) -> str:
        query = " AND ".join([clause.to_query(nested=True) for clause in self.clauses])
        return "(" + query + ")" if nested else query


OperatorTypes = OrOperator | AndOperator


class BaseQuery(BaseModel, Generic[QualifierTypes, AdvancedQualifierTypes]):
    qualifiers: Sequence[QualifierTypes] = Field(description="The qualifiers of the search query.", default_factory=list)
    advanced: OrOperator[AdvancedQualifierTypes] | AndOperator[AdvancedQualifierTypes] | None = Field(
        default=None, description="A nested operator for advanced search."
    )

    """The `BaseQuery` operator is the base class for all queries."""

    def add_qualifier(self, qualifier: QualifierTypes | None) -> Self:
        if qualifier is None:
            return self
        self.qualifiers = [*self.qualifiers, qualifier]
        return self

    def to_query(self) -> str:
        rendered_qualifiers = " ".join([qualifier.to_query() for qualifier in self.qualifiers])
        rendered_advanced = self.advanced.to_query(True) if self.advanced else ""
        return f"{rendered_qualifiers} {rendered_advanced}".strip()
