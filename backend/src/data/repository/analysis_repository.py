import uuid
from typing import List

from sqlmodel import Session, select

from src.data.model.analysis_model import Analysis


class AnalysisRepository:
    def __init__(self, session: Session):
        """
        Constructor of the AnalysisRepository class

        Args:
            session (Session): SQLModel session
        """
        self.session: Session = session

    def create(self, analysis: Analysis) -> Analysis:
        """
        Add a new analysis in the database

        Args:
            analysis (Analysis): The analysis we want to add

        Returns:
            Analysis: The analysis added
        """
        self.session.add(analysis)
        self.session.commit()
        self.session.refresh(analysis)
        return analysis

    def get_all(self) -> list[Analysis]:
        """
        Get all the analyses stored in the database

        Returns:
            list[Analysis]: All database analyses
        """
        statement = select(Analysis)
        results: List[Analysis] = list(self.session.exec(statement).all())
        return results

    def get_by_patient_login(self, patient_login: str) -> list[Analysis]:
        """
        Get all the analyses associated to a patient's login

        Args:
            patient_login (str): The patient's login

        Returns:
            list[Analysis]: All database analyses of the patient
        """
        statement = select(Analysis).where(Analysis.patient_login == patient_login)
        results: List[Analysis] = list(self.session.exec(statement).all())
        return results

    def get_by_id(self, id: uuid.UUID) -> Analysis:
        """
        Get the analysis corresponding to the given id

        Args:
            id (uuid.UUID): The analysis ID

        Returns:
            Analysis: The analysis associated with the ID

        Raises:
            NoResultFound: If no analysis was found
        """
        statement = select(Analysis).where(Analysis.id == id)
        result: Analysis = self.session.exec(statement).one()
        return result

    def delete_by_id(self, id: uuid.UUID) -> None:
        """
        Delete the analysis corresponding to the given id

        Args:
            id (uuid.UUID): The analysis ID

        Raises:
            NoResultFound: If no analysis was found
        """
        statement = select(Analysis).where(Analysis.id == id)
        result: Analysis = self.session.exec(statement).one()

        self.session.delete(result)
        self.session.commit()

    def delete_by_patient_login(self, patient_login: str) -> bool:
        """
        Delete all the analyses corresponding to the given patient's login

        Args:
            patient_login (str): The patient's login

        Returns:
            bool: True if the deletion was successful, False otherwise
        """
        statement = select(Analysis).where(Analysis.patient_login == patient_login)
        results: List[Analysis] = list(self.session.exec(statement).all())

        if len(results) == 0:
            return False

        for result in results:
            self.session.delete(result)

        self.session.commit()
        return True

    def update_analysis_metrics(
        self,
        id: uuid.UUID,
        area_left_lung: float,
        area_right_lung: float,
        asymetric_score: float,
    ) -> Analysis:
        """
        Update an analysis in the database

        Args:
            id (uuid.UUID): The analysis ID
            area_left_lung (float): Surface area of the left lung
            area_right_lung (float): Surface area of the right lung
            asymetric_score (float): Asymmetry score calculated

        Returns:
            Analysis: The updated analysis

        Raises:
            NoResultFound: If no analysis was found
        """
        statement = select(Analysis).where(Analysis.id == id)
        result: Analysis = self.session.exec(statement).one()

        result.area_left_lung = area_left_lung
        result.area_right_lung = area_right_lung
        result.asymetric_score = asymetric_score

        self.session.add(result)
        self.session.commit()
        self.session.refresh(result)

        return result
